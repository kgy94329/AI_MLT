<p align="center"> <img src=https://user-images.githubusercontent.com/58832219/208357285-ec18b7f7-5f3d-4f66-91f5-e3367926a4f1.png> </p>

# MyLittleFairyTales

## 목차

# 프로젝트 개요

## 컨셉

내가 만드는 4컷 동화

## 프로젝트 기간

- 2022.09.14 ~ 2022.09.30

## 시스템 아키텍처 & 개발환경

![image](https://user-images.githubusercontent.com/58832219/208357643-e40950e3-ca77-42c5-a51a-6a5d54698607.png)

## 플로우차트

![image](https://user-images.githubusercontent.com/58832219/208357700-649661f1-81b8-4eb7-bdd0-9b6ae5b67a99.png)

## 프로젝트 시연

[![image](https://user-images.githubusercontent.com/58832219/208358545-a5fcefe4-635a-4242-bcf5-cf3e93726a4a.png)](https://youtu.be/iiQZ5y_8GDE)

# AI 주요 기능

(__*이탤릭 볼드체*__ 는 제가 구현한 기능입니다.)

## __*Stable Diffusion*__

![image](https://user-images.githubusercontent.com/58832219/208357932-2b5e40bc-03b4-41a0-8d50-1f0e8c743862.png)

- __*Hugging Face의 CompVis/stable-diffusion-v1-4모델을 활용*__
- __*입력받은 한국어 배경 설명 문장을 구글 번역 api를 활용하여 영문으로 변환*__
- __*영문으로 변환한 텍스트에 동화속 삽화의 느낌을 주기 위해 이미지 생성시 “oil painting style” 조건을 추가*__
- __*생성된 이미지를 base64 형식 바이트 문자열로 인코딩하여 데이터 전송*__
- __*문제점 및 해결*__
    - __*stable diffusion 모델을 로컬 pc에서 구동하기에는 리소스가 부족*__
    - __*가장 가벼운 모델을 사용해도 모델을 불러오는 과정에서 OOM이 발생*__
    - __*구글 Colab에서는 모델이 정상적으로 구동되는 것을 확인*__
    - __*Colab에 flask서버를 열어서 로컬 pc와 통신하도록 함*__

## Remove Background

![image](https://user-images.githubusercontent.com/58832219/208357987-682b571d-ac88-4431-bc4e-224f57ce314d.png)

[활용 코드](https://github.com/danielgatis/rembg)

- rembg를 활용하여 사람 객체만 누끼를 땀
- 추출된 누끼데이터에서 사람이 있는 부분만 하얀색으로 변환하여 마스크 이미지를 생성
- 생성된 마스크 이미지를 서버로 전송

## ImageBlend

![image](https://user-images.githubusercontent.com/58832219/208358100-8bab4f14-bb96-4e01-b1a0-4eb581e68319.png)

[참고논문](https://openaccess.thecvf.com/content_WACV_2020/papers/Zhang_Deep_Image_Blending_WACV_2020_paper.pdf)

- Image Blend 모델을 활용하여 생성된 배경 이미지와 사용자의 원본 사진, 마스크 이미지를 합성
- 합성된 이미지를 클라이언트로 전송
