#!/usr/bin/env python3
import argparse
import imageio.v2 as iio
from math import floor
import numpy as np
import os
from PIL import Image, ImageOps, ImageFont, ImageDraw
import random
import requests
import soundfile as sf
from tqdm import tqdm
import warnings

# ignore avx2 warnings on nix
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
    import pygame


# summons a new soundfile block generator
def genblocks(get, bs):
    return sf.blocks(get, blocksize=bs)


# compress rows into smaller chunks
def row(row, fps, peak):
    # flatten channels if not mono
    if row.ndim > 1:
        row = row.mean(axis=1)

    size = floor(len(row) / fps)

    return list(
        map(
            lambda x: int(
                (np.sqrt(np.mean(row[x * size : x * size + size] ** 2)) / float(peak))
                * 255
            ),
            list(range(fps)),
        )
    )


def run():
    print("anxvis ᓚ₍ ^. .^₎")

    # Define CLI arguments
    parser = argparse.ArgumentParser(description="an ethereal audio visualizer")

    parser.add_argument("input", metavar="INPUT", type=str, help="path for audio input")
    parser.add_argument(
        "output", metavar="OUTPUT", type=str, help="path for video output"
    )
    parser.add_argument(
        "-t",
        metavar="FONT",
        type=str,
        default="Cartograph CF",
        help="font name",
        dest="font_name",
    )
    parser.add_argument(
        "-f", metavar="FPS", type=int, default=60, help="framerate", dest="fps"
    )
    parser.add_argument(
        "-s", metavar="SCALE", type=int, default=4, help="scale factor", dest="scale"
    )

    args = parser.parse_args()

    pygame.init()

    # arguments to variables
    input = args.input
    output = args.output
    fps = args.fps
    scale = args.scale

    # fetch random words
    print("fetching dictionary...", end="", flush=True)

    def dictionary():
        fetch = "https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt"
        response = requests.get(fetch)
        return response.content.splitlines()

    words = dictionary()
    print(" done!")

    # audio analysis
    def analyze(audio):
        full_audio = sf.read(audio)

        # finds samples per video frame
        sample_rate = int(full_audio[1])
        audio_frames = int(sample_rate / fps)
        video_length = int(len(full_audio[0]) / float(audio_frames))

        # locates peak amplitude (rms) in audio
        blocks = genblocks(input, audio_frames)
        big = [np.sqrt(np.mean(b**2.0)) for b in blocks]
        peak_amplitude = max(big)

        return (sample_rate, audio_frames, video_length, peak_amplitude)

    print("let me see that audio file...")
    (sr, af, vl, pa) = analyze(input)
    print(
        str(sr)
        + "hz, "
        + str(af)
        + " samples/frame, "
        + "{:.2}".format(pa)
        + " rms max"
    )

    # configures canvas
    print("set the camera... ", end="", flush=True)
    buffer = np.zeros((int(fps / 2), fps))

    query_font = pygame.font.match_font(args.font_name)
    font = ImageFont.truetype(query_font, float(fps * scale) / 30.0)
    overlay = Image.new("RGBA", (fps * scale, fps * scale), (255, 255, 255, 0))

    # opens output video
    writer = iio.get_writer(output, format="mp4", mode="I", fps=fps, audio_path=input)

    # displays preview
    screen = pygame.display.set_mode((fps * scale, fps * scale), 0, 32)

    print("start!")
    with tqdm(total=vl) as pbar:
        for i, block in enumerate(genblocks(input, af)):
            # create new row and append to buffer
            compressed = row(block, fps, pa)
            buffer = np.vstack((compressed, buffer))[:-1]

            # mirror effect
            ibuffer = np.flip(buffer)
            doubled = np.vstack((ibuffer, buffer))

            # render and stylize full buffer
            base = (
                ImageOps.colorize(
                    Image.fromarray(np.uint8(doubled), "L").resize(
                        (fps * scale, fps * scale), resample=Image.NEAREST
                    ),
                    black="#f2dce9",
                    white="#590f3c",
                )
            ).convert("RGBA")

            # scroll previous frame of overlay
            overlay = overlay.transform(overlay.size, Image.AFFINE, (1, 0, -2, 0, 1, 0))

            # add text to overlay
            if i % 2 == 0:
                draw = ImageDraw.Draw(overlay)

                draw.text(
                    (random.randint(0, fps * scale), random.randint(0, fps * scale)),
                    random.choice(words).decode("utf-8").split("	")[1],
                    font=font,
                    fill="#651e5a",
                )

            # composite images and write to file
            img = Image.alpha_composite(base, overlay)
            writer.append_data(np.asarray(img))

            # converts image for pygame
            rimg = img.tobytes("raw", "RGBA")
            pimg = pygame.image.fromstring(rimg, (fps * scale, fps * scale), "RGBA")

            # updates image on pygame
            screen.blit(pimg, (0, 0))
            pygame.display.update()

            # increases progress bar
            pbar.update(1)
    # close file
    writer.close()
    print("done! =ᗢ=")
