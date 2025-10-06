import streamlit as st
import requests
import io
import time
from PIL import Image
import base64

st.set_page_config(page_title="Зображення у Відео UA", page_icon="🎬")

# API endpoints для різних сервісів
REPLICATE_API = "https://api.replicate.com/v1/predictions"
STABLE_VIDEO_API = "https://api-inference.huggingface.co/models/stabilityai/stable-video-diffusion-img2vid"

def generate_video_replicate(image, motion_description, duration=3):
    """Генерація відео через Replicate API"""
    headers = {
        "Authorization": f"Bearer {st.secrets.get('REPLICATE_TOKEN', '')}",
        "Content-Type": "application/json"
    }
    
    # Конвертуємо зображення в base64
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    payload = {
        "version": "25a2413bf4e23c1cc6e5e07a9005c80b8c17d344a8a9bc4ed8e1fea5ed88d8a2",
        "input": {
            "image": f"data:image/jpeg;base64,{img_base64}",
            "prompt": motion_description,
            "duration": duration,
            "fps": 8
        }
    }
    
    response = requests.post(REPLICATE_API, json=payload, headers=headers)
    if response.status_code == 201:
        prediction = response.json()
        return prediction["id"]
    else:
        st.error(f"Помилка API: {response.status_code}")
        return None

def check_prediction_status(prediction_id):
    """Перевірка статусу генерації"""
    headers = {
        "Authorization": f"Bearer {st.secrets.get('REPLICATE_TOKEN', '')}",
    }
    
    response = requests.get(f"{REPLICATE_API}/{prediction_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def generate_video_huggingface(image, motion_description):
    """Альтернативний метод через HuggingFace"""
    headers = {
        "Authorization": f"Bearer {st.secrets.get('HF_TOKEN', '')}"
    }
    
    # Конвертуємо зображення
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    
    files = {"inputs": buffered.getvalue()}
    data = {"parameters": {"motion_bucket_id": 127}}
    
    response = requests.post(STABLE_VIDEO_API, headers=headers, files=files, data=data)
    
    if response.status_code == 200:
        return response.content
    return None

# Основний інтерфейс
st.title("🎬 Зображення у Відео — Оживляємо картинки")
st.markdown("Перетворюйте зображення на живі відео за допомогою ШІ")

# Вибір джерела зображення
col1, col2 = st.columns(2)

with col1:
    st.subheader("📤 Завантаження зображення")
    
    tab1, tab2 = st.tabs(["📁 Завантажити файл", "🔗 Із FLUX генератора"])
    
    with tab1:
        uploaded_image = st.file_uploader(
            "Оберіть зображення",
            type=['png', 'jpg', 'jpeg'],
            help="Підтримуються формати: PNG, JPG, JPEG"
        )
        
        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption="Завантажене зображення", use_column_width=True)
    
    with tab2:
        st.markdown("**Ваш FLUX генератор:**")
        st.link_button(
            "🎨 Створити зображення в FLUX",
            "https://realtime-flux-ru.streamlit.app",
            help="Відкриється в новій вкладці"
        )
        
        st.info("💡 Створіть зображення в FLUX генераторі, збережіть його і завантажте тут")

with col2:
    if 'uploaded_image' in locals() and uploaded_image:
        st.subheader("⚙️ Налаштування анімації")
        
        motion_description = st.text_area(
            "🎬 Опис руху",
            "Камера повільно наближається, об'єкти злегка хитаються",
            height=100,
            help="Опишіть як має рухатися зображення"
        )
        
        duration = st.slider(
            "⏱️ Тривалість (секунди)",
            min_value=2,
            max_value=6,
            value=3,
            help="Тривалість відеоролика"
        )
        
        fps = st.selectbox(
            "🎯 Якість",
            [("Швидко (8 FPS)", 8), ("Стандарт (12 FPS)", 12), ("Високе (24 FPS)", 24)],
            index=1
        )
        
        # Приклади описів руху
        with st.expander("💡 Приклади описів руху"):
            examples = [
                "Камера повільно рухається вперед",
                "Легке хитання на вітрі",
                "М'які хвилі на воді",
                "Плавне обертання навколо об'єкта",
                "Частинки пилу літають у повітрі",
                "Мерехтливе світло і тіні",
                "Хмари повільно рухаються",
                "Відблиски грають на поверхні",
                "Листя трепеще на дереві",
                "Дим піднімається вгору"
            ]
            
            for example in examples:
                if st.button(f"📝 {example}", key=f"example_{example}"):
                    motion_description = example
                    st.rerun()

# Генерація відео
if 'uploaded_image' in locals() and uploaded_image and st.button("🎬 Створити відео", type="primary"):
    if not motion_description.strip():
        st.error("❌ Будь ласка, опишіть бажаний рух")
    else:
        # Перевіряємо наявність API токенів
        if not st.secrets.get("REPLICATE_TOKEN") and not st.secrets.get("HF_TOKEN"):
            st.error("❌ Необхідний API токен. Додайте REPLICATE_TOKEN або HF_TOKEN в налаштування.")
        else:
            with st.spinner("🎬 Створюємо відео... Це може зайняти 1-3 хвилини"):
                try:
                    # Пробуємо Replicate API
                    if st.secrets.get("REPLICATE_TOKEN"):
                        prediction_id = generate_video_replicate(image, motion_description, duration)
                        
                        if prediction_id:
                            # Очікуємо завершення
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i in range(60):  # Максимум 5 хвилин
                                status = check_prediction_status(prediction_id)
                                
                                if status and status["status"] == "succeeded":
                                    video_url = status["output"]
                                    st.success("✅ Відео готове!")
                                    
                                    # Показуємо відео
                                    st.video(video_url)
                                    
                                    # Інформація про генерацію
                                    st.info(f"""
                                    **Параметри відео:**
                                    - 🎬 Рух: {motion_description}
                                    - ⏱️ Тривалість: {duration} сек
                                    - 🎯 FPS: {fps[1]}
                                    - 📐 Розмір: {image.size[0]}×{image.size[1]}
                                    """)
                                    break
                                    
                                elif status and status["status"] == "failed":
                                    st.error("❌ Помилка генерації відео")
                                    break
                                    
                                progress_bar.progress((i + 1) / 60)
                                status_text.text(f"Обробка... {i*5} секунд")
                                time.sleep(5)
                    
                    # Альтернативно пробуємо HuggingFace
                    elif st.secrets.get("HF_TOKEN"):
                        video_bytes = generate_video_huggingface(image, motion_description)
                        if video_bytes:
                            st.success("✅ Відео готове!")
                            st.video(video_bytes)
                        else:
                            st.error("❌ Помилка генерації через HuggingFace")
                    
                except Exception as e:
                    st.error(f"❌ Помилка: {str(e)}")

# Інформаційна панель
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🎨 Підтримувані формати", "JPG, PNG")

with col2:
    st.metric("⏱️ Час генерації", "1-3 хв")

with col3:
    st.metric("🎬 Тривалість відео", "2-6 сек")

# Інструкції
with st.expander("📚 Як користуватися"):
    st.markdown("""
    ### 🚀 Швидкий старт:
    
    1. **Створіть зображення** в нашому FLUX генераторі
    2. **Збережіть** зображення на комп'ютер
    3. **Завантажте** тут через "Завантажити файл"
    4. **Опишіть рух** який хочете бачити
    5. **Натисніть** "Створити відео"
    6. **Дочекайтеся** результату (1-3 хвилини)
    
    ### 💡 Поради для кращих результатів:
    
    - Використовуйте чіткі, деталізовані зображення
    - Описуйте прості, плавні рухи
    - Починайте з коротких відео (2-3 секунди)
    - Експериментуйте з різними описами
    
    ### 🎬 Приклади успішних промптів:
    
    - "Вода тече вниз по каменю"
    - "Вогонь танцює в каміні"
    - "Хмари пливуть по небу"
    - "Квіти хитаються на вітрі"
    """)

# Поради та підказки
with st.expander("🎯 Поради для кращої анімації"):
    st.markdown("""
    ### Найкраще працює з:
    - 🌊 **Природні сцени** (вода, вогонь, хмари)
    - 🌸 **Рослини** (квіти, дерева, трава)
    - 🏔️ **Пейзажі** (гори, поля, озера)
    - 🎨 **Портрети** (легкий рух волосся, одягу)
    
    ### Уникайте:
    - Складні технічні об'єкти
    - Багато дрібних деталей
    - Різкі геометричні форми
    - Текст і написи
    """)

st.markdown("---")
st.markdown("**🎬 Створено з використанням Stable Video Diffusion та Replicate API**")
st.markdown("**🇺🇦 Українська версія для творчої спільноти**")
