import os
from dotenv import load_dotenv
from supabase import create_client, Client
import cloudinary
import cloudinary.uploader
import bcrypt


# 1. Carrega as variáveis do arquivo .env para o sistema
load_dotenv()

# 2. Configuração do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. Configuração do Cloudinary
cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure = True
)

def fazer_upload_imagem(arquivo):
    try:
        # Se for um arquivo do Streamlit, lemos os bytes
        if hasattr(arquivo, 'read'):
            conteudo = arquivo.read()
        else:
            conteudo = arquivo

        # Faz o upload com OTIMIZAÇÃO
        resultado = cloudinary.uploader.upload(
            conteudo,
            folder="obra_social", # Organiza as fotos em uma pasta
            transformation=[
                # 1. Limita a largura para 1200px (tamanho ótimo para web)
                # O 'limit' garante que se a foto for menor, ela não será esticada.
                {'width': 1200, 'crop': "limit"}, 
                
                # 2. Qualidade Automática (q_auto)
                # O Cloudinary analisa a foto e aplica a maior compressão sem perda visível.
                {'quality': "auto"},
                
                # 3. Formato Automático (f_auto)
                # Converte para formatos modernos como WebP ou AVIF se o navegador aceitar.
                {'fetch_format': "auto"}
            ]
        )
        
        url = resultado.get("secure_url")
        print(f"✅ Foto otimizada e salva: {url}")
        return url
        
    except Exception as e:
        print(f"❌ ERRO NO CLOUDINARY: {e}")
        return None

# --- Exemplo de como você usará isso no arquivo principal ---
# url_foto = fazer_upload_imagem("foto_igreja.jpg")
# print(f"Link da foto: {url_foto}")

def gerar_senha_criptografada(senha_plana):
    # Transforma a senha em um código seguro
    salt = bcrypt.gensalt()
    senha_hash = bcrypt.hashpw(senha_plana.encode('utf-8'), salt)
    return senha_hash.decode('utf-8')

def verificar_senha(senha_digitada, senha_hash_do_banco):
    # Compara a senha digitada com o código do banco
    return bcrypt.checkpw(senha_digitada.encode('utf-8'), senha_hash_do_banco.encode('utf-8'))