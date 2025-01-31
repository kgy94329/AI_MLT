# Packages
import pdb
import numpy as np
import torch
import torch.optim as optim
from PIL import Image
import matplotlib.pyplot as plt
from skimage.io import imsave
from utils import compute_gt_gradient, make_canvas_mask, numpy2tensor, laplacian_filter_tensor, \
                  MeanShift, Vgg16, gram_matrix
from timeit import default_timer as timer
from datetime import timedelta
import os
import gc
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

ss=300
ts=512
x_start=400
y_start=235
gpu_id=0
num_steps=800

# Define Loss Functions
mse = torch.nn.MSELoss()
# Import VGG network for computing style and content loss
mean_shift = MeanShift(gpu_id)
vgg = Vgg16().to(gpu_id)


# Define LBFGS optimizer
def get_input_optimizer(first_pass_img):
    optimizer = optim.LBFGS([first_pass_img.requires_grad_()])
    return optimizer

###################################
########### First Pass ###########x
###################################
def first_step(source_file, mask_file, target_file):

    # Default weights for loss functions in the first pass
    grad_weight = 1e4; style_weight = 1e4; content_weight = 1; tv_weight = 1e-6

    # Load Images
    source_img = np.array(Image.open(source_file).convert('RGB').resize((ss, ss)))
    target_img = np.array(Image.open(target_file).convert('RGB').resize((ts, ts)))
    mask_img = np.array(Image.open(mask_file).convert('L').resize((ss, ss)))
    mask_img[mask_img>0] = 1

    # Make Canvas Mask
    canvas_mask = make_canvas_mask(x_start, y_start, target_img, mask_img)
    canvas_mask = numpy2tensor(canvas_mask, gpu_id)
    canvas_mask = canvas_mask.squeeze(0).repeat(3,1).view(3,ts,ts).unsqueeze(0)

    # Compute Ground-Truth Gradients
    gt_gradient = compute_gt_gradient(x_start, y_start, source_img, target_img, mask_img, gpu_id)

    # Convert Numpy Images Into Tensors
    source_img = torch.from_numpy(source_img).unsqueeze(0).transpose(1,3).transpose(2,3).float().to(gpu_id)
    target_img = torch.from_numpy(target_img).unsqueeze(0).transpose(1,3).transpose(2,3).float().to(gpu_id)
    input_img = torch.randn(target_img.shape).to(gpu_id)

    mask_img = numpy2tensor(mask_img, gpu_id)
    mask_img = mask_img.squeeze(0).repeat(3,1).view(3,ss,ss).unsqueeze(0)

    optimizer = get_input_optimizer(input_img)


    run = [0]
    while run[0] <= num_steps:

        def closure():
            # Composite Foreground and Background to Make Blended Image
            blend_img = torch.zeros(target_img.shape).to(gpu_id)
            blend_img = input_img*canvas_mask + target_img*(canvas_mask-1)*(-1)
            
            # Compute Laplacian Gradient of Blended Image
            pred_gradient = laplacian_filter_tensor(blend_img, gpu_id)
            
            # Compute Gradient Loss
            grad_loss = 0
            for c in range(len(pred_gradient)):
                grad_loss += mse(pred_gradient[c], gt_gradient[c])
            grad_loss /= len(pred_gradient)
            grad_loss *= grad_weight
            
            
            # Compute Content Loss
            blend_obj = blend_img[:,:,int(x_start-source_img.shape[2]*0.625):int(x_start+source_img.shape[2]*0.625), int(y_start-source_img.shape[3]*0.5):int(y_start+source_img.shape[3]*0.5)]
            source_object_features = vgg(mean_shift(source_img*mask_img))
            blend_object_features = vgg(mean_shift(blend_obj*mask_img))
            content_loss = content_weight * mse(blend_object_features.relu2_2, source_object_features.relu2_2)
            content_loss *= content_weight
            
            # Compute TV Reg Loss
            tv_loss = torch.sum(torch.abs(blend_img[:, :, :, :-1] - blend_img[:, :, :, 1:])) + \
                    torch.sum(torch.abs(blend_img[:, :, :-1, :] - blend_img[:, :, 1:, :]))
            tv_loss *= tv_weight
            
            # Compute Total Loss and Update Image
            loss = grad_loss + content_loss + tv_loss
            optimizer.zero_grad()
            loss.backward()
            
            run[0] += 1
            return loss

        optimizer.step(closure)

    # clamp the pixels range into 0 ~ 255
    input_img.data.clamp_(0, 255)

    # Make the Final Blended Image
    blend_img = torch.zeros(target_img.shape).to(gpu_id)
    blend_img = input_img*canvas_mask + target_img*(canvas_mask-1)*(-1) 
    blend_img_np = blend_img.transpose(1,3).transpose(1,2).cpu().data.numpy()[0]

    # Save image from the first pass
    name = source_file.split('/')[1].split('_')[0]
    imsave('static/images//'+str(name)+'_first_pass.png', blend_img_np.astype(np.uint8))

    return name 
###################################
########### Second Pass ###########
###################################

def second_step(target_file, name):
    # Default weights for loss functions in the second pass
    style_weight = 1e7; content_weight = 1; tv_weight = 1e-6
    ss = 512; ts = 512
    # num_steps = num_steps

    first_pass_img_file = 'static/images/'+str(name)+'_first_pass.png'
    first_pass_img = np.array(Image.open(first_pass_img_file).convert('RGB').resize((ss, ss)))
    target_img = np.array(Image.open(target_file).convert('RGB').resize((ts, ts)))
    first_pass_img = torch.from_numpy(first_pass_img).unsqueeze(0).transpose(1,3).transpose(2,3).float().to(gpu_id)
    target_img = torch.from_numpy(target_img).unsqueeze(0).transpose(1,3).transpose(2,3).float().to(gpu_id)

    optimizer = get_input_optimizer(first_pass_img)

    print('Optimizing...')
    run = [0]
    while run[0] <= 30:
        
        def closure():
            # Compute Loss Loss    
            target_features_style = vgg(mean_shift(target_img))
            target_gram_style = [gram_matrix(y) for y in target_features_style]
            blend_features_style = vgg(mean_shift(first_pass_img))
            blend_gram_style = [gram_matrix(y) for y in blend_features_style]
            style_loss = 0
            for layer in range(len(blend_gram_style)):
                style_loss += mse(blend_gram_style[layer], target_gram_style[layer])
            style_loss /= len(blend_gram_style)
            style_loss *= style_weight
            
            # Compute Content Loss
            content_features = vgg(mean_shift(first_pass_img))
            content_loss = content_weight * mse(blend_features_style.relu2_2, content_features.relu2_2)
            
            # Compute Total Loss and Update Image
            loss = style_loss + content_loss
            optimizer.zero_grad()
            loss.backward()
                        
            run[0] += 1
            return loss
        
        optimizer.step(closure)

    # clamp the pixels range into 0 ~ 255
    first_pass_img.data.clamp_(0, 255)

    # Make the Final Blended Image
    input_img_np = first_pass_img.transpose(1,3).transpose(1,2).cpu().data.numpy()[0]

    # Save image from the second pass
    imsave('static/images/'+str(name)+'_second_pass.png', input_img_np.astype(np.uint8))


def blendImage(source_file, mask_file, target_file):
    try:
        print('Image Blending Start')
        start = timer()
        name = first_step(source_file, mask_file, target_file)
        end = timer()
        print('First Blending is done', timedelta(seconds=end-start))
        start2 = timer()
        second_step(target_file, name)
        end2 = timer()
        print(timedelta(seconds=end2-start2), timedelta(seconds=end2-start))
        gc.collect()
    except Exception as e:
        return e
# source_file = r'C:\Users\HP\Desktop\workspace\Project\FairyTale\AI_MLT\fairytale\static\data\origin2.png'
# mask_file = r'C:\Users\HP\Desktop\workspace\Project\FairyTale\AI_MLT\fairytale\static\data\mask_image2.png'
# target_file = r'C:\Users\HP\Desktop\workspace\Project\FairyTale\AI_MLT\fairytale\static\data\back_ground.png'

# blendImage(source_file, mask_file, target_file)