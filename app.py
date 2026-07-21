import streamlit as st
from conexao import supabase

# Configuração básica da página
st.set_page_config(page_title="Igreja Corpus Christi", layout="centered")

# --- MENU LATERAL ---
menu = st.sidebar.radio("Navegação", ['Quem Somos', 'Notícias', 'Horários das Missas', 'Fale Conosco'])

# --- 1. SEÇÃO: QUEM SOMOS ---
if menu == 'Quem Somos':
    st.title("⛪ Nossa Igreja")
    response = supabase.table("institucional").select("*").limit(1).execute()
    
    if response.data:
        info = response.data[0]
        
        # Verifique se o nome da coluna no banco é exatamente 'url_foto_igreja'
        link_foto = info.get("url_foto_igreja")
        
        if link_foto:
            st.image(link_foto, use_container_width=True)
        
        st.markdown(f"### Sobre nós\n{info['texto_quem_somos']}")
# --- 2. SEÇÃO: NOTÍCIAS (ATUALIZADA PARA MÍDIAS MISTAS) ---
elif menu == 'Notícias':
    st.title("📰 Notícias e Eventos")

    # Busca notícias no banco
    noticias = supabase.table("noticias_eventos").select("*").order("data_publicacao", desc=True).execute().data

    if noticias:
        # Controle do Carrossel de Notícias
        if 'news_index' not in st.session_state:
            st.session_state.news_index = 0
        
        # Controle do índice da mídia (foto ou vídeo)
        if 'media_index' not in st.session_state:
            st.session_state.media_index = 0

        # Botões de navegação entre Notícias
        col_ant, col_prox = st.columns([1, 1])
        
        if col_ant.button("⬅️ Notícia Anterior"):
            st.session_state.news_index = (st.session_state.news_index - 1) % len(noticias)
            st.session_state.media_index = 0 # Reseta galeria ao mudar notícia
            st.rerun()
        
        if col_prox.button("Próxima Notícia ➡️"):
            st.session_state.news_index = (st.session_state.news_index + 1) % len(noticias)
            st.session_state.media_index = 0 # Reseta galeria ao mudar notícia
            st.rerun()

        st.divider()

        # Exibe a notícia atual
        noticia_atual = noticias[st.session_state.news_index]
        
        st.subheader(noticia_atual['titulo'])
        st.caption(f"📅 Publicado em: {noticia_atual['data_publicacao'][:10]}")

        # --- LÓGICA DE EXIBIÇÃO DE GALERIA MISTA (FOTO E VÍDEO) ---
        if noticia_atual['url_midia']:
            # Divide a string de URLs pelas vírgulas
            lista_midia = [m.strip() for m in noticia_atual['url_midia'].split(",") if m.strip()]
            
            if lista_midia:
                # Se houver mais de uma mídia, mostra contador e navegação
                if len(lista_midia) > 1:
                    st.write(f"📦 Mídia {st.session_state.media_index + 1} de {len(lista_midia)}")
                
                midia_atual = lista_midia[st.session_state.media_index]

                # Identifica se é vídeo do YouTube ou Foto
                if "youtube.com" in midia_atual or "youtu.be" in midia_atual:
                    st.video(midia_atual)
                else:
                    st.image(midia_atual, use_container_width=True)
                
                # Botões de navegação da galeria (só aparecem se tiver mais de 1 mídia)
                if len(lista_midia) > 1:
                    c1, c2, c3 = st.columns([1, 2, 1])
                    if c1.button("⬅️ Ant.", key="btn_gal_ant"):
                        st.session_state.media_index = (st.session_state.media_index - 1) % len(lista_midia)
                        st.rerun()
                    if c3.button("Prox. ➡️", key="btn_gal_prox"):
                        st.session_state.media_index = (st.session_state.media_index + 1) % len(lista_midia)
                        st.rerun()

        # Conteúdo da notícia
        st.markdown(f"**Sobre este evento:**")
        st.write(noticia_atual['conteudo'])
        
        st.divider()
        st.info(f"Mostrando notícia {st.session_state.news_index + 1} de {len(noticias)}")

    else:
        st.info("Nenhuma notícia publicada no momento.")

# --- 3. SEÇÃO: HORÁRIOS DAS MISSAS ---
elif menu == 'Horários das Missas':
    st.title("📅 Escala de Missas")

    missas = supabase.table("escala_missas").select("*").order("paroquia").execute().data

    if missas:
        for m in missas:
            with st.container():
                st.markdown(f"### {m['paroquia']}")
                col1, col2, col3 = st.columns(3)
                col1.metric("Dia", m['dia_semana'])
                col2.metric("Horário", m['horario'][:5]) # Mostra apenas HH:MM
                col3.metric("Padre", m['nome_padre'] or "A definir")
                
                # Alerta de observação se existir
                if m.get('observacao'):
                    st.warning(f"⚠️ **Aviso:** {m['observacao']}")
                st.divider()
    else:
        st.info("A escala de missas ainda não foi carregada.")

# --- 4. SEÇÃO: FALE CONOSCO ---
elif menu == 'Fale Conosco':
    st.title("🙏 Fale Conosco / Pedidos de Oração")
    st.write("Use o formulário abaixo para entrar em contato ou pedir orações.")

    with st.form("form_ajuda", clear_on_submit=True):
        nome = st.text_input("Seu Nome")
        telefone = st.text_input("Seu Telefone / WhatsApp", placeholder="(00) 00000-0000")
        tipo = st.selectbox("Assunto", ['Oração', 'Ajuda', 'Dúvida'])
        mensagem = st.text_area("Sua Mensagem")
        
        submit = st.form_submit_button("Enviar Mensagem")

        if submit:
            if nome and mensagem and telefone: 
                dados_pedido = {
                    "nome": nome,
                    "telefone": telefone, 
                    "tipo": tipo,
                    "mensagem": mensagem,
                    "status": "Pendente"
                }             
                try:
                    supabase.table("pedidos_ajuda").insert(dados_pedido).execute()
                    st.success("Sua mensagem foi enviada com sucesso! Fique com Deus.")
                except Exception as e:
                    st.error(f"Erro ao enviar: {e}")
            else:
                st.warning("Por favor, preencha todos os campos obrigatórios (Nome, Telefone e Mensagem).")

# --- RODAPÉ NO MENU LATERAL ---
st.sidebar.markdown("---")
st.sidebar.caption("⛪ Obra Social - Igreja")