import streamlit as st
import requests
import io
import time
import base64
import json
from PIL import Image

st.set_page_config(page_title="Справжнє Оживлення Зображень UA", page_icon="🎬")

# Робочі API для справжнього оживлення
REPLICATE_LTX_API = "https://api.replicate.com/v1/predictions"
SEGMIND_LTX_API = "https://api.segmind.com/v1/ltx-video"
FAL_API = "https://fal.run/fal-ai/ltx-video"
MODAL_API = "https://lightricks-ltx-video-distilled.modal.run"

def generate_video_replicate_ltx(image, prompt, duration=5):
    """Генерація через Replicate LTX-Video (найкраща якість)"""
    try:
        # Конвертуємо зображення в base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        headers = {
            "Authorization": f"Bearer {st.secrets.get('REPLICATE_TOKEN', '')}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "version": "ac9693cdb61a5d8b185f00db93b7b27aca7c845ce7d04b78aefbeaf6e7f1d4c6",  # LTX-Video 0.9.7 distilled
            "input": {
                "image": f"data:image/jpeg;base64,{img_base64}",
                "prompt": prompt,
                "num_frames": int(duration * 8),  # 8 FPS для швидкості
                "width": min(image.width, 704),
                "height": min(image.height, 512), 
                "num_inference_steps": 8,  # Distilled model потребує менше кроків
                "guidance_scale": 2.5
            }
        }
        
        response = requests.post(REPLICATE_LTX_API, json=payload, headers=headers)
        
        if response.status_code == 201:
            prediction = response.json()
            return prediction["id"], "replicate_ltx"
        else:
            st.error(f"Replicate API помилка: {response.status_code} - {response.text}")
            return None, None
            
    except Exception as e:
        st.error(f"Помилка Replicate LTX: {e}")
        return None, None

def generate_video_segmind_ltx(image, prompt):
    """Генерація через Segmind LTX-Video API"""
    try:
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        headers = {
            "x-api-key": st.secrets.get('SEGMIND_TOKEN', ''),
            "Content-Type": "application/json"
        }
        
        payload = {
            "image": f"data:image/jpeg;base64,{img_base64}",
            "prompt": prompt,
            "num_frames": 25,
            "fps": 8,
            "seed": -1,
            "guidance_scale": 3.0,
            "num_inference_steps": 8
        }
        
        response = requests.post(SEGMIND_LTX_API, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("video_url"), "segmind_direct"
        else:
            return None, None
            
    except Exception as e:
        return None, None

def generate_video_fal_ltx(image, prompt):
    """Генерація через FAL LTX-Video"""
    try:
        import fal_client
        
        # Завантажуємо зображення на FAL
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        
        result = fal_client.submit(
            "fal-ai/ltx-video",
            arguments={
                "image_url": fal_client.upload(buffered, "image/jpeg"),
                "prompt": prompt,
                "num_frames": 25,
                "fps": 8,
                "seed": -1,
                "guidance_scale": 3.0,
                "num_inference_steps": 8
            },
        )
        
        return result.get("video").get("url"), "fal_direct"
        
    except Exception as e:
        return None, None

def check_replicate_status(prediction_id):
    """Перевірка статусу Replicate генерації"""
    try:
        headers = {
            "Authorization": f"Bearer {st.secrets.get('REPLICATE_TOKEN', '')}",
        }
        
        response = requests.get(f"{REPLICATE_LTX_API}/{prediction_id}", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        return None
        
    except Exception as e:
        return None

def create_demo_with_ltx_style(image, prompt):
    """Демо режим, що імітує LTX-Video стиль оживлення"""
    import numpy as np
    from PIL import ImageEnhance, ImageFilter, ImageDraw
    
    frames = []
    base_frames = 25  # ~3 секунди при 8 FPS
    
    # Аналізуємо промпт для типу руху
    prompt_lower = prompt.lower()
    
    # Визначаємо області руху на основі промпту
    animate_hair = any(word in prompt_lower for word in ['волосся', 'hair', 'коса', 'локони'])
    animate_clothes = any(word in prompt_lower for word in ['одяг', 'clothes', 'сукня', 'рубашка', 'куртка'])
    animate_water = any(word in prompt_lower for word in ['вода', 'water', 'море', 'річка', 'дощ'])
    animate_fire = any(word in prompt_lower for word in ['вогонь', 'fire', 'полум\'я', 'свічка'])
    animate_eyes = any(word in prompt_lower for word in ['очі', 'eyes', 'погляд', 'моргання'])
    animate_smoke = any(word in prompt_lower for word in ['дим', 'smoke', 'пара', 'туман'])
    
    for i in range(base_frames):
        frame = image.copy()
        
        # Створюємо маски для різних областей
        width, height = frame.size
        
        if animate_hair:
            # Імітуємо рух волосся - легкі хвилі
            wave_strength = np.sin(i * 0.3) * 2
            # Застосовуємо деформацію до верхньої частини
            top_region = frame.crop((0, 0, width, height // 3))
            # Простий зсув для імітації руху волосся
            offset = int(wave_strength)
            if offset != 0:
                shifted = Image.new('RGB', top_region.size, (0, 0, 0))
                if offset > 0:
                    shifted.paste(top_region.crop((offset, 0, width, height // 3)), (0, 0))
                else:
                    shifted.paste(top_region.crop((0, 0, width + offset, height // 3)), (-offset, 0))
                frame.paste(shifted, (0, 0))
        
        if animate_clothes:
            # Імітуємо рух одягу - легке коливання
            cloth_wave = np.sin(i * 0.25) * 1.5
            # Застосовуємо до середньої частини зображення
            mid_region = frame.crop((0, height // 3, width, 2 * height // 3))
            offset = int(cloth_wave)
            if offset != 0:
                shifted = Image.new('RGB', mid_region.size, (0, 0, 0))
                if offset > 0:
                    shifted.paste(mid_region.crop((offset, 0, width, height // 3)), (0, 0))
                else:
                    shifted.paste(mid_region.crop((0, 0, width + offset, height // 3)), (-offset, 0))
                frame.paste(shifted, (0, height // 3))
        
        if animate_water:
            # Імітуємо рух води - рипплі ефект
            ripple_strength = np.sin(i * 0.4) * 3
            # Застосовуємо хвилястий ефект
            enhancer = ImageEnhance.Brightness(frame)
            brightness = 1.0 + np.sin(i * 0.5) * 0.05
            frame = enhancer.enhance(brightness)
            
            # Додаємо легке розмиття для ефекту води
            if i % 3 == 0:
                frame = frame.filter(ImageFilter.GaussianBlur(0.5))
        
        if animate_fire:
            # Імітуємо полум'я - мерехтіння
            flicker = 1.0 + np.sin(i * 0.8) * 0.1 + np.random.normal(0, 0.02)
            enhancer = ImageEnhance.Brightness(frame)
            frame = enhancer.enhance(flicker)
            
            # Додаємо теплі тони
            enhancer = ImageEnhance.Color(frame)
            frame = enhancer.enhance(1.1)
        
        if animate_eyes:
            # Імітуємо моргання - зміна яскравості очей
            if i % 12 == 0:  # Моргання кожні 1.5 секунди
                # Затемнюємо центральну область (очі)
                eye_region = frame.crop((width//4, height//4, 3*width//4, 2*height//3))
                enhancer = ImageEnhance.Brightness(eye_region)
                darkened = enhancer.enhance(0.7)
                frame.paste(darkened, (width//4, height//4))
        
        if animate_smoke:
            # Імітуємо рух диму - плавний підйом
            smoke_offset = i * 0.5
            # Застосовуємо градієнт прозорості
            overlay = Image.new('RGBA', frame.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Створюємо ефект диму
            for y in range(0, height, 20):
                alpha = int(30 * np.sin(y * 0.1 + smoke_offset))
                if alpha > 0:
                    draw.rectangle([0, y, width, y+10], fill=(200, 200, 200, alpha))
            
            frame = Image.alpha_composite(frame.convert('RGBA'), overlay).convert('RGB')
        
        # Додаємо загальний тремтіння для живості
        global_tremor = np.random.normal(0, 0.3)
        if abs(global_tremor) > 0.1:
            offset_x = int(global_tremor)
            offset_y = int(np.random.normal(0, 0.2))
            
            shifted = Image.new('RGB', frame.size, (0, 0, 0))
            paste_x = max(0, offset_x)
            paste_y = max(0, offset_y)
            crop_x = max(0, -offset_x)
            crop_y = max(0, -offset_y)
            
            cropped = frame.crop((crop_x, crop_y, frame.width + crop_x, frame.height + crop_y))
            shifted.paste(cropped, (paste_x, paste_y))
            frame = shifted
        
        frames.append(frame)
    
    # Створюємо GIF з високим FPS для плавності
    output = io.BytesIO()
    frames[0].save(output, format='GIF', 
                   save_all=True, append_images=frames[1:], 
                   duration=120,  # 120ms = ~8 FPS
                   loop=0)
    output.seek(0)
    
    return output.getvalue()

# Основний інтерфейс
st.title("🎬 Справжнє Оживлення Зображень — LTX-Video Клон")
st.markdown("**Справжнє AI оживлення об'єктів у зображеннях, як LTX-Video модель**")

# Інформація про API
with st.expander("🔑 Налаштування API для професійного оживлення"):
    st.markdown("""
    ### 🚀 Для справжнього LTX-Video оживлення потрібен один з API:
    
    **Replicate (рекомендується):**
    - Реєстрація: https://replicate.com
    - API ключ: Account → API tokens  
    - Вартість: ~$0.01 за відео
    - У Secrets: `REPLICATE_TOKEN = "r8_..."`
    
    **Segmind (швидше):**
    - Реєстрація: https://segmind.com
    - API ключ: Dashboard → API Keys
    - Вартість: ~$0.005 за відео
    - У Secrets: `SEGMIND_TOKEN = "ваш_ключ"`
    
    **FAL AI (найновіші моделі):**
    - Реєстрація: https://fal.ai
    - Безкоштовні кредити на старт
    - У Secrets: `FAL_KEY = "ваш_ключ"`
    """)

# Вибір режиму роботи
mode = st.radio(
    "🎯 Режим роботи:",
    [
        "🎨 Демо (імітація LTX-стилю) - БЕЗКОШТОВНО",
        "🚀 Професійний (справжній LTX-Video) - ПОТРІБЕН API",
    ]
)

# Завантаження зображення
uploaded_image = st.file_uploader(
    "📤 Завантажте зображення для оживлення",
    type=['png', 'jpg', 'jpeg'],
    help="Краще працює з портретами, людьми, тваринами"
)

if uploaded_image:
    image = Image.open(uploaded_image)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(image, caption="🖼️ Оригінальне зображення", use_column_width=True)
        
        # Аналіз зображення
        st.info(f"""
        **Параметри зображення:**
        - 📐 Розмір: {image.width} × {image.height}
        - 📄 Формат: {image.format}
        - 🎨 Режим: {image.mode}
        """)
    
    with col2:
        st.subheader("⚙️ Налаштування оживлення")
        
        # Промпт для оживлення (дуже важливий!)
        prompt = st.text_area(
            "🎬 Опис того, що має оживитися",
            "Волосся м'якого хитається на вітрі, очі дивляться, легкий рух одягу",
            height=120,
            help="Детально опишіть що і як має рухатися в зображенні"
        )
        
        if "Професійний" in mode:
            duration = st.slider("⏱️ Тривалість (секунди)", 2, 6, 4)
            quality = st.selectbox("🎯 Якість", ["Стандарт (8 FPS)", "Висока (24 FPS)"])
        
        # Приклади промптів для оживлення
        with st.expander("💡 Приклади для різних типів зображень"):
            examples = {
                "👥 Портрети": [
                    "Волосся м'якого хитається, очі моргають, легкий рух одягу",
                    "Легкий посмішка з'являється, волосся рухається на вітрі", 
                    "Очі дивляться в різні сторони, губи злегка рухаються"
                ],
                "🌊 Природа": [
                    "Вода тече і хвилюється, відблиски сонця грають",
                    "Листя хитається на дереві, трава коливається",
                    "Хмари повільно рухаються по небу"
                ],
                "🔥 Об'єкти": [
                    "Полум'я танцює і мерехтить",
                    "Дим піднімається вгору спіральними рухами",
                    "Квіти хитаються на стеблі"
                ],
                "🐕 Тварини": [
                    "Вуха рухаються, хвіст виляє, очі дивляться",
                    "Шерсть хитається на вітрі, ніс сопе",
                    "Голова повертається, лапи злегка рухаються"
                ]
            }
            
            for category, prompts in examples.items():
                st.markdown(f"**{category}:**")
                for prompt_example in prompts:
                    if st.button(f"📝 {prompt_example}", key=f"prompt_{hash(prompt_example)}"):
                        prompt = prompt_example
                        st.rerun()

    # Кнопка генерації
    if st.button("🎬 ОЖИВИТИ ЗОБРАЖЕННЯ", type="primary", use_container_width=True):
        if not prompt.strip():
            st.error("❌ Опишіть що має рухатися в зображенні!")
        else:
            if "Демо" in mode:
                with st.spinner("🎨 Створюємо оживлення в стилі LTX... 20 секунд"):
                    animation_data = create_demo_with_ltx_style(image, prompt)
                    
                    if animation_data:
                        st.success("✅ Оживлення готове!")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.image(image, caption="Оригінал")
                        
                        with col2:
                            st.image(animation_data, caption="🎬 Оживлене зображення")
                        
                        st.download_button(
                            "📥 Завантажити GIF",
                            animation_data,
                            f"animated_{int(time.time())}.gif",
                            "image/gif"
                        )
                        
                        st.info(f"""
                        **Параметри оживлення:**
                        - 🎬 Промпт: {prompt}
                        - ⏱️ Тривалість: 3 секунди
                        - 🎯 FPS: 8 кадрів/сек
                        - 📄 Формат: Анімований GIF
                        - 🔧 Технологія: Імітація LTX-стилю
                        """)
                    else:
                        st.error("❌ Помилка створення оживлення")
                        
            else:  # Професійний режим
                api_available = (st.secrets.get("REPLICATE_TOKEN") or 
                               st.secrets.get("SEGMIND_TOKEN") or 
                               st.secrets.get("FAL_KEY"))
                
                if not api_available:
                    st.error("""
                    ❌ **Потрібен API ключ!**
                    
                    Додайте один з токенів у Settings → Secrets:
                    - `REPLICATE_TOKEN = "r8_..."`
                    - `SEGMIND_TOKEN = "ваш_ключ"`  
                    - `FAL_KEY = "ваш_ключ"`
                    """)
                else:
                    with st.spinner("🚀 Створюємо професійне LTX-Video... 1-3 хвилини"):
                        video_url = None
                        service = None
                        
                        # Спробуємо різні API по черзі
                        if st.secrets.get("REPLICATE_TOKEN"):
                            task_id, service = generate_video_replicate_ltx(image, prompt, duration)
                            
                            if task_id:
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                for i in range(60):  # 5 хвилин максимум
                                    status = check_replicate_status(task_id)
                                    
                                    if status:
                                        if status.get("status") == "succeeded":
                                            video_url = status.get("output")
                                            break
                                        elif status.get("status") == "failed":
                                            st.error("❌ Помилка Replicate генерації")
                                            break
                                    
                                    progress_bar.progress((i + 1) / 60)
                                    status_text.text(f"LTX-Video обробка... {i*5} секунд")
                                    time.sleep(5)
                        
                        elif st.secrets.get("SEGMIND_TOKEN"):
                            video_url, service = generate_video_segmind_ltx(image, prompt)
                        
                        elif st.secrets.get("FAL_KEY"):
                            video_url, service = generate_video_fal_ltx(image, prompt)
                        
                        if video_url:
                            st.success("✅ Професійне LTX-Video готове!")
                            st.video(video_url)
                            
                            st.info(f"""
                            **Параметри LTX-Video:**
                            - 🎬 Промпт: {prompt}
                            - ⏱️ Тривалість: {duration} сек
                            - 🎯 Якість: {quality}
                            - 🔧 Сервіс: {service}
                            - 📄 Формат: MP4 відео
                            - 🚀 Технологія: Справжній LTX-Video
                            """)
                        else:
                            st.error("❌ Всі API недоступні. Спробуйте пізніше або використайте демо режим.")

# Поради
with st.expander("🎯 Поради для найкращого оживлення"):
    st.markdown("""
    ### 📸 Найкраще працює з:
    - **Портрети людей** (волосся, очі, одяг)
    - **Тварини** (шерсть, вуха, хвости)
    - **Природні сцени** (вода, вогонь, дим, листя)
    - **Чіткі зображення** без розмиття
    
    ### 🎬 Як писати промпти:
    - **Конкретно**: "волосся хитається" замість "рух"
    - **Деталізовано**: "очі моргають, губи злегка рухаються"  
    - **Природно**: "легкий вітер рухає одяг і волосся"
    - **Фокусовано**: не більше 2-3 типів руху одночасно
    
    ### ⚡ Для демо режиму:
    - Використовує ключові слова для розпізнання типу анімації
    - Волосся, одяг, вода, вогонь, очі, дим анімуються по-різному
    - Результат схожий на LTX-Video стиль
    """)

st.markdown("---")
st.markdown("**🎬 Демо режим: Імітація LTX-Video стилю | Професійний: Справжній LTX-Video**")
st.markdown("**🇺🇦 Створено для української творчої спільноти**")
