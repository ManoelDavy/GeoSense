from ultralytics import YOLO 
import cv2

# carrega o modelo pré-treinado
model = YOLO("yolov8n.pt")

# faz a detecção em uma imagem
results = model("retrato-de-voluntarios-que-organizaram-doacoes-para-instituicoes-de-caridade_23-2149230571.jpg", show=True)

img = results[0].plot()
img = cv2.resize(img, (800, 600))  # ajusta o tamanho

cv2.imshow("YOLO", img)

while True:
    if cv2.waitKey(1) == 27:  # 27 = ESC
        break

cv2.destroyAllWindows()