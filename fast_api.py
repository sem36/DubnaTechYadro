from fastapi import FastAPI, File, UploadFile, HTTPException
from fastai.vision.all import load_learner, PILImage
from pathlib import Path
from PIL import Image

app = FastAPI()

model_path = Path("/home/sem/Documents/pet.pkl")
learn = load_learner(model_path)

class_translation = {
    "american_bulldog": "Американский бульдог",
    "american_pit_bull_terrier": "Американский питбультерьер",
    "basset_hound": "Басет-хаунд",
    "beagle": "Бигль",
    "boxer": "Боксер",
    "chihuahua": "Чихуахуа",
    "english_cocker_spaniel": "Английский кокер-спаниель",
    "english_setter": "Английский сеттер",
    "german_shorthaired": "Немецкий короткошёрстный",
    "great_pyrenees": "Пиренейская горная собака",
    "havanese": "Гаванская собака",
    "japanese_chin": "Японский чих",
    "keeshond": "Кишонд",
    "leonberger": "Леонбергер",
    "miniature_pinscher": "Миниатюрный пинчер",
    "newfoundland": "Ньюфаундленд",
    "pomeranian": "Померанский шпиц",
    "pug": "Мопс",
    "saint_bernard": "Святой Бернар",
    "samoyed": "Самоед",
    "scottish_terrier": "Шотландский терьер",
    "shiba_inu": "Шиба-ину",
    "staffordshire_bull_terrier": "Стаффордширский бультерьер",
    "wheaten_terrier": "Пшеничный терьер",
    "yorkshire_terrier": "Йоркширский терьер",

    "Abyssinian": "Абиссинская кошка",
    "Bengal": "Бенгальская кошка",
    "Birman": "Бирманская кошка",
    "Bombay": "Бомбейская кошка",
    "British_shorthair": "Британская короткошёрстная кошка",
    "Egyptian_mau": "Египетская мау",
    "Main_coon": "Мейн-кун",
    "Persian": "Персидская кошка",
    "Ragdoll": "Рэгдолл",
    "Russian_blue": "Русская голубая кошка",
    "Siamese": "Сиамская кошка",
    "Sphynx": "Сфинкс"
}

CONFIDENCE_THRESHOLD = 0.7

def get_image_description(image: Image.Image):
    pred_class, pred_idx, outputs = learn.predict(PILImage.create(image))
    predicted_class_ru = class_translation.get(pred_class, pred_class)
    
    outputs_list = outputs.tolist()
    print("Outputs from the model:", outputs_list)
    
    max_prob = max(outputs_list)
    
    if max_prob < CONFIDENCE_THRESHOLD:
        return "Бродяга", -1, {}
    
    class_probabilities = {class_translation.get(cls, cls): prob for cls, prob in zip(learn.dls.vocab, outputs_list) if prob > 0.001}
    
    return predicted_class_ru, pred_idx, class_probabilities

@app.post("/process_image/")
async def process_image(file: UploadFile = File(...)):
    try:
        image = Image.open(file.file).convert("RGB")
    except IOError:
        raise HTTPException(status_code=400, detail="File is not a valid image.")
    
    description, pred_idx, class_probabilities = get_image_description(image)
    
    return {"prediction": description, "pred_index": pred_idx, "probabilities": class_probabilities}