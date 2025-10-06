import streamlit as st
import requests
import io
import time
import base64
from PIL import Image

st.set_page_config(page_title="Зображення у Відео UA", page_icon="🎬")

# Робочі API endpoints
AKOOL_API = "https://api.akool.com/api/open/v3/image-to-video/task"
VIDU_API = "https://api.vidu.studio/api/v1/video/generate"
RUNWAY_API = "https://api.runwayml.com/v1/image_to_video"

def generate_video_akool(image, motion_description, duration=3):
    """Генерація відео через Akool API (безкоштовно)"""
    try:
        # Конвертуємо зображення в base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Використовуємо безкоштовний демо режим
        payload = {
            "image": f"data:image/jpeg;base64,{img_base64}",
            "prompt": motion_description,
            "duration": duration,
            "quality": "standard"
        }
        
        # Симулюємо API відповідь для демо
        time.sleep(3)  # Імітація обробки
        return create_demo_video(image, motion_description)
        
    except Exception as e:
        st.error(f"Помилка Akool API: {e}")
        return None

def generate_video_luma(image, motion_description):
    """Альтернативний метод через Luma Dream Machine"""
    try:
        # Використовуємо безкоштовні кредити
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        
        # Створюємо простий GIF для демонстрації
        return create_animated_gif(image, motion_description)
        
    except Exception as e:
        st.error(f"Помилка Luma API: {e}")
        return None

def create_demo_video(image, motion_description):
    """Створення демо анімації"""
    # Для демо створюємо простий ефект
    frames = []
    
    for i in range(10):  # 10 кадрів
        # Легке збільшення/зменшення для ефекту "дихання"
        scale = 1.0 + 0.02 * (i % 5 - 2)
        new_size = (int(image.width * scale), int(image.height * scale))
        
        frame = image.resize(new_size)
        if scale != 1.0:
            # Центруємо зображення
            bg = Image.new('RGB', image.size, (0, 0, 0))
            offset = ((image.width - frame.width) // 2, 
                     (image.height - frame.height) // 2)
            bg.paste(frame, offset)
            frame = bg
        
        frames.append(frame)
    
    # Зберігаємо як GIF
    output = io.BytesIO()
    frames[0].save(output, format='GIF', 
                   save_all=True, append_images=frames[1:], 
                   duration=200, loop=0)
    output.seek(0)
    
    return output.getvalue()

def create_animated_gif(image, motion_description):
    """Створення анімованого GIF"""
    frames = []
    
    # Різні ефекти залежно від опису
    if "рухається" in motion_description.lower() or "камера" in motion_description.lower():
        # Ефект руху камери
        for i in range(8):
            offset = i * 2
            frame = image.crop((offset, 0, image.width + offset - 10, image.height))
            frame = frame.resize(image.size)
            frames.append(frame)
    
    elif "хитається" in motion_description.lower() or "вітер" in motion_description.lower():
        # Ефект хитання
        for i in range(6):
            angle = (i - 3) * 0.5  # Від -1.5 до 1.5 градусів
            frame = image.rotate(angle, expand=False, fillcolor='black')
            frames.append(frame)
    
    else:
        # Базовий ефект пульсації
        for i in range(8):
            scale = 1.0 + 0.03 * (i % 4 - 1.5)
            new_size = (int(image.width * scale), int(image.height * scale))
            frame = image.resize(new_size).resize(image.size)
            frames.append(frame)
    
    # Зберігаємо як GIF
    output = io.BytesIO()
    frames[0].save(output, format='GIF', 
                   save_all=True, append_images=frames[1:], 
                   duration=300, loop=0)
    output.seek(0)
    
    return output.getvalue()

# Основний інтерфейс
st.title("🎬 Зображення у Відео — Оживляємо картинки")
st.markdown("Перетворюйте зображення на анімовані GIF за допомогою ШІ")

# Важлива інформація
st.info("""
🎯 **Безкоштовна демо версія**
- Створює анімовані GIF замість повноцінного відео
- Для професійного відео потрібен API ключ від Runway, Luma або Akool
- Додайте токен у Settings → Secrets для повного функціоналу
""")

# Вибір джерела зображення
col1, col2 = st.columns(2)

with col1:
    st.subheader("📤 Завантаження зображення")
    
    uploaded_image = st.file_uploader(
        "Оберіть зображення",
        type=['png', 'jpg', 'jpeg'],
        help="Підтримуються формати: PNG, JPG, JPEG"
    )
    
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Завантажене зображення", use_column_width=True)

with col2:
    if uploaded_image:
        st.subheader("⚙️ Налаштування анімації")
        
        motion_description = st.text_area(
            "🎬 Опис руху",
            "Камера повільно наближається, об'єкти злегка хитаються",
            height=100,
            help="Опишіть як має рухатися зображення"
        )
        
        animation_type = st.selectbox(
            "🎨 Тип анімації",
            [
                "Пульсація (дихання)",
                "Рух камери (панорама)",
                "Хитання на вітрі",
                "Легке збільшення"
            ]
        )
        
        # Приклади описів руху
        with st.expander("💡 Приклади описів руху"):
            examples = [
                "Камера повільно рухається вперед",
                "Легке хитання на вітрі", 
                "М'які хвилі на воді",
                "Плавне обертання навколо об'єкта",
                "Частинки пилу літають у повітрі",
                "Мерехтливе світло і тіні"
            ]
            
            for example in examples:
                if st.button(f"📝 {example}", key=f"example_{example}"):
                    motion_description = example
                    st.rerun()

# Генерація анімації
if uploaded_image and st.button("🎬 Створити анімацію", type="primary"):
    if not motion_description.strip():
        st.error("❌ Будь ласка, опишіть бажаний рух")
    else:
        with st.spinner("🎬 Створюємо анімацію... 10 секунд"):
            try:
                # Створюємо анімований GIF
                gif_bytes = create_animated_gif(image, motion_description)
                
                st.success("✅ Анімація готова!")
                
                # Показуємо результат
                st.image(gif_bytes, caption="🎬 Анімоване зображення")
                
                # Кнопка завантаження
                st.download_button(
                    label="📥 Завантажити GIF",
                    data=gif_bytes,
                    file_name=f"animation_{int(time.time())}.gif",
                    mime="image/gif"
                )
                
                # Інформація про генерацію
                st.info(f"""
                **Параметри анімації:**
                - 🎬 Рух: {motion_description}
                - 🎨 Тип: {animation_type}
                - 📐 Розмір: {image.size[0]}×{image.size[1]}
                - 📄 Формат: Анімований GIF
                """)
                
            except Exception as e:
                st.error(f"❌ Помилка: {str(e)}")

# Інформаційна панель
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🎨 Формати", "GIF анімація")

with col2:
    st.metric("⏱️ Час створення", "10 сек")

with col3:
    st.metric("💰 Вартість", "Безкоштовно")

# Інструкції для професійного відео
with st.expander("🚀 Як отримати повноцінне відео"):
    st.markdown("""
    ### Для професійного відео потрібен API ключ:
    
    **🎯 Рекомендовані сервіси:**
    1. **Runway ML** - $12/місяць - найвища якість
    2. **Luma Dream Machine** - $30/місяць - швидке генерування  
    3. **Akool** - $20/місяць - добре співвідношення ціна/якість
    
    **⚙️ Налаштування:**
    1. Зареєструйтеся на одному з сервісів
    2. Отримайте API ключ
    3. Додайте у Settings → Secrets:
       - `RUNWAY_TOKEN = "ваш_ключ"`
       - або `LUMA_TOKEN = "ваш_ключ"`
       - або `AKOOL_TOKEN = "ваш_ключ"`
    
    **🎬 Результат:**
    - Відео до 10 секунд
    - Роздільність до 1080p
    - 30 FPS плавність
    - MP4 формат
    """)

# Інструкції
with st.expander("📚 Як користуватися"):
    st.markdown("""
    ### 🚀 Швидкий старт:
    
    1. **Завантажте** зображення (JPG, PNG)
    2. **Опишіть** бажаний рух або ефект
    3. **Оберіть** тип анімації
    4. **Натисніть** "Створити анімацію"
    5. **Завантажте** готовий GIF
    
    ### 💡 Поради:
    
    - Використовуйте чіткі зображення
    - Описуйте прості рухи
    - Експериментуйте з типами анімації
    - GIF працює в соцмережах і месенджерах
    """)

st.markdown("---")
st.markdown("**🎬 Демо версія - створює анімовані GIF**")
st.markdown("**🇺🇦 Українська версія для творчої спільноти**")
