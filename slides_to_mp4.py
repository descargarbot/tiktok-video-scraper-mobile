def resize_image(image_path, target_size):
    img = Image.open(image_path)
    img.thumbnail(target_size, Image.Resampling.LANCZOS)
    new_img = Image.new("RGB", target_size, (0, 0, 0))
    new_img.paste(img, ((target_size[0] - img.width) // 2, (target_size[1] - img.height) // 2))
    temp_path = f"resized_{os.path.basename(image_path)}"
    new_img.save(temp_path)
    return temp_path

def tiktok_create_slideshow(audio, images, output_file):

    for image in images:
        if not Path(image).is_file():
            raise FileNotFoundError(f"img not found: {image}")
    
    if not Path(audio).is_file():
        raise FileNotFoundError(f"file not found: {audio}")
    
    result = subprocess.run(
        ["ffprobe", "-i", audio, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"],
        capture_output=True, text=True, check=True
    )
    audio_duration = float(result.stdout.strip())

    num_images = len(images)
    duration_per_image = audio_duration / num_images

    target_size = (1280, 720)

    resized_images = [resize_image(image, target_size) for image in images]

    filter_complex = ""
    inputs = []
    for i, image in enumerate(resized_images):
        inputs.extend(["-loop", "1", "-t", str(duration_per_image), "-i", image])
        filter_complex += f"[{i}:v]scale={target_size[0]}:{target_size[1]},setsar=1[v{i}];"

    filter_complex += "".join(f"[v{i}]" for i in range(len(resized_images)))
    filter_complex += f"concat=n={num_images}:v=1:a=0[outv]"

    subprocess.run([
        "ffmpeg", "-y", 
        *inputs, 
        "-i", audio,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", f"{len(resized_images)}:a",
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", "-shortest", output_file
    ], check=True)

    for temp_image in resized_images:
        Path(temp_image).unlink(missing_ok=True)


# async way

async def resize_image_async(image_path, target_size):
    def _resize(path, size):
        img = Image.open(path)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        new_img = Image.new("RGB", size, (0, 0, 0))
        new_img.paste(img, ((size[0] - img.width) // 2, (size[1] - img.height) // 2))
        temp_path = f"resized_{os.path.basename(path)}"
        new_img.save(temp_path)
        return temp_path
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _resize, image_path, target_size)

async def get_audio_duration(audio_path):
    process = await asyncio.create_subprocess_exec(
        "ffprobe", "-i", audio_path, 
        "-show_entries", "format=duration", 
        "-v", "quiet", "-of", "csv=p=0",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await process.communicate()
    return float(stdout.decode().strip())

async def run_ffmpeg(cmd):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)

async def tiktok_create_slideshow_async(audio, images, output_file):
    try:
        for image in images:
            if not Path(image).is_file():
                raise FileNotFoundError(f"img not found: {image}")
        
        if not Path(audio).is_file():
            raise FileNotFoundError(f"file not found: {audio}")
        
        audio_duration = await get_audio_duration(audio)

        num_images = len(images)
        duration_per_image = audio_duration / num_images

        target_size = (1280, 720)

        resize_tasks = [resize_image_async(image, target_size) for image in images]
        resized_images = await asyncio.gather(*resize_tasks)

        filter_complex = ""
        inputs = []
        for i, image in enumerate(resized_images):
            inputs.extend(["-loop", "1", "-t", str(duration_per_image), "-i", image])
            filter_complex += f"[{i}:v]scale={target_size[0]}:{target_size[1]},setsar=1[v{i}];"

        filter_complex += "".join(f"[v{i}]" for i in range(len(resized_images)))
        filter_complex += f"concat=n={num_images}:v=1:a=0[outv]"

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-i", audio,
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", f"{len(resized_images)}:a",
            "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p",
            "-shortest", output_file
        ]

        await run_ffmpeg(cmd)

    finally:
        for temp_image in resized_images:
            Path(temp_image).unlink(missing_ok=True)
