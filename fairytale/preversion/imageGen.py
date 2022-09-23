import os
import sys
import torch
from torch import autocast
from diffusers import StableDiffusionPipeline
from googletrans import Translator
import gc

class imageGen:
    def __init__(self):
        self.model_id = 'CompVis/stable-diffusion-v1-4'
        if torch.cuda.is_available():
            self.device = 'cuda'
            print('cuda가 연결되었습니다.')
        else:
            os.exit('cuda가 인식되지 않습니다.')
        self.pipe = StableDiffusionPipeline.from_pretrained(self.model_id, use_auth_token='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')
        self.translator = Translator()
        print('image 생성 준비 완료')

    def getPipe(self):
        self.pipe = self.pipe.to('cuda')
        return self.pipe

    def Prompt_ko(self, textdata):
        text_result = self.translator.translate(textdata, src = 'ko', dest='en')
        return text_result.text

    def makeImg(self, text):
        prompt = 'cartoon: ' + text
        print(prompt)
        with autocast(self.device):
            image = self.pipe(prompt, guidance_scale=7.5)["sample"][0]  
            
        image.save("astronaut_rides_horse2.jpg")
        return image


if __name__ == '__main__':
    with torch.no_grad():
        torch.cuda.empty_cache()
        gc.collect()
        ig = imageGen()
        ig.makeImg(ig.Prompt_ko('해질녘 해변가'))
        
        print('done')