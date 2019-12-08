from scipy.interpolate import CubicSpline
import numpy as np
import time
import torch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
from torchvision import utils
from tqdm import tqdm
import cv2
import random
import sys
import math
from model import StyledGenerator
from generate import get_mean_style

standard_normal_distribution = torch.distributions.normal.Normal(0, 1)

RESOLUTION = 256
STEP = int(math.log(RESOLUTION, 2)) - 2

SAMPLE_COUNT = 10 # Number of distinct objects to generate and interpolate between
TRANSITION_FRAMES = 180

LATENT_CODE_SIZE = 512

codes = standard_normal_distribution.sample((SAMPLE_COUNT + 1, LATENT_CODE_SIZE)).numpy()

codes[0, :] = codes[-1, :] # Make animation periodic
spline = CubicSpline(np.arange(SAMPLE_COUNT + 1), codes, axis=0, bc_type='periodic')

def create_image_sequence():
    frame_index = 0
    progress_bar = tqdm(total=SAMPLE_COUNT * TRANSITION_FRAMES)

    for sample_index in range(SAMPLE_COUNT):
        for step in range(TRANSITION_FRAMES):
            code = torch.tensor(spline(float(sample_index) + step / TRANSITION_FRAMES), dtype=torch.float32, device=device).reshape(1, -1)
            
            image = generator(
                code,
                step=STEP,
                alpha=1,
                mean_style=mean_style,
                style_weight=0.7,
            )
            
            utils.save_image(image, 'images/frame-{:05d}.png'.format(frame_index), normalize=True, range=(-1, 1))
            
            frame_index += 1
            progress_bar.update()
    
    print("\n\nUse this command to create a video:\n")
    print('ffmpeg -framerate 30 -i images/frame-%05d.png -c:v libx264 -profile:v high -crf 19 -pix_fmt yuv420p video.mp4')



generator = StyledGenerator(LATENT_CODE_SIZE).to(device)
generator.load_state_dict(torch.load('checkpoint/train_step-7.model')['g_running'])
generator.eval()

mean_style = get_mean_style(generator, device)
create_image_sequence()