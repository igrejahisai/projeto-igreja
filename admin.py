import streamlit as st
from conexao import supabase, fazer_upload_imagem, gerar_senha_criptografada, verificar_senha
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO INICIAL E ESTILIZAÇÃO
# ==========================================
st.set_page_config(
    page_title="Painel de Gestão - Obra Social",
    page_icon="⚙️",
    layout="wide"
)

# --- INICIALIZAÇÃO DA SESSÃO ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = None

def realizar_logout():
    st.session_state.logado = False
    st.session_state.usuario = None
    st.rerun()

# ==========================================
# 2. TELA DE LOGIN
# ==========================================
if not st.session_state.logado:
    st.title("🔐 Acesso Restrito - Coordenação")
    st.write("Bem-vinda! Por favor, identifique-se para gerenciar a obra social.")
    
    with st.form("login_form"):
        email_input = st.text_input("E-mail Cadastrado")
        senha_input = st.text_input("Senha", type="password")
        botao_entrar = st.form_submit_button("Entrar no Sistema")
        
        if botao_entrar:
            # Consulta o usuário no Supabase
            resposta = supabase.table("usuarios_coordenacao").select("*").eq("email", email_input).execute()
            
            if resposta.data:
                usuario_db = resposta.data[0]
                # Verifica a senha com criptografia Bcrypt
                if verificar_senha(senha_input, usuario_db['senha']):
                    st.session_state.logado = True
                    st.session_state.usuario = usuario_db
                    st.rerun()
                else:
                    st.error("Senha incorreta. Tente novamente.")
            else:
                st.error("E-mail não encontrado no cadastro da equipe.")
    st.stop()

# ==========================================
# 3. REGRA DE SEGURANÇA: TROCA DE SENHA
# ==========================================
if verificar_senha("123456", st.session_state.usuario['senha']):
    st.warning("🚨 SEGURANÇA: Sua senha atual é provisória (123456). Por favor, crie uma nova senha pessoal.")
    
    with st.form("troca_senha_obrigatoria"):
        nova_s = st.text_input("Nova Senha", type="password", help="Mínimo 6 caracteres")
        confirma_s = st.text_input("Confirme a Nova Senha", type="password")
        
        if st.form_submit_button("Salvar Nova Senha"):
            if nova_s == confirma_s and len(nova_s) >= 6:
                hash_novo = gerar_senha_criptografada(nova_s)
                supabase.table("usuarios_coordenacao").update({"senha": hash_novo}).eq("id", st.session_state.usuario['id']).execute()
                st.success("Senha atualizada com sucesso! Faça login novamente.")
                realizar_logout()
            else:
                st.error("As senhas não coincidem ou são muito curtas.")
    st.stop()

# ==========================================
# 4. LAYOUT DO PAINEL (APÓS LOGIN)
# ==========================================
st.sidebar.title("MENU ADMIN")
st.sidebar.write(f"Conectado como: \n**{st.session_state.usuario['email']}**")
st.sidebar.write(f"Perfil: {st.session_state.usuario['role'].upper()}")
st.sidebar.button("Sair do Sistema", on_click=realizar_logout)

st.title("⚙️ Gestão da Obra Social")

# Configuração Dinâmica de Abas
abas_nomes = ["Pedidos de Ajuda", "Notícias/Eventos", "Escala de Missas", "Institucional"]
if st.session_state.usuario['role'] == 'mestre':
    abas_nomes.append("Gerenciar Equipe")

tab_pedidos, tab_noticias, tab_missas, tab_inst, *tab_equipe = st.tabs(abas_nomes)

# ==========================================
# --- ABA 1: PEDIDOS DE AJUDA ---
# ==========================================
with tab_pedidos:
    st.header("📋 Gestão de Pedidos e Orações")
    pedidos = supabase.table("pedidos_ajuda").select("*").order("data_abertura", desc=True).execute().data
    
    if not pedidos:
        st.info("Nenhum pedido registrado até o momento.")
    else:
        for p in pedidos:
            emoji_st = {"Pendente": "🔴", "Em andamento": "🟡", "Concluído": "🟢"}
            with st.expander(f"{emoji_st.get(p['status'])} {p['nome']} - {p['tipo']}"):
                st.write(f"**Mensagem do Fiel:** {p['mensagem']}")
                
                # Link do WhatsApp
                tel = p.get('telefone')
                if tel:
                    t_limpo = ''.join(filter(str.isdigit, tel))
                    st.markdown(f"**📞 Contato:** [{tel}](https://wa.me/55{t_limpo})")
                
                st.write("---")
                
                # ANOTAÇÕES INTERNAS
                st.write("📝 **Anotações da Coordenação / Histórico:**")
                anot_atual = p.get('anotacoes_coordenacao') or ""
                
                if p['status'] != 'Concluído':
                    nova_anot = st.text_area("Descreva o atendimento realizado:", value=anot_atual, key=f"an_{p['id']}")
                    if st.button("Salvar Anotação", key=f"ban_{p['id']}"):
                        supabase.table("pedidos_ajuda").update({"anotacoes_coordenacao": nova_anot}).eq("id", p['id']).execute()
                        st.success("Anotação salva!")
                        st.rerun()
                else:
                    st.info(anot_atual if anot_atual else "Nenhuma anotação registrada.")

                st.write("---")
                st.caption(f"Aberto em: {p['data_abertura']}")
                
                col_btn_at = st.columns(2)
                if p['status'] == 'Pendente' and col_btn_at[0].button("Iniciar Atendimento", key=f"iat_{p['id']}"):
                    supabase.table("pedidos_ajuda").update({"status": "Em andamento"}).eq("id", p['id']).execute()
                    st.rerun()
                elif p['status'] == 'Em andamento' and col_btn_at[0].button("✅ Concluir Chamado", key=f"cch_{p['id']}"):
                    supabase.table("pedidos_ajuda").update({
                        "status": "Concluído", 
                        "data_conclusao": datetime.now().isoformat()
                    }).eq("id", p['id']).execute()
                    st.rerun()

# ==========================================
# --- ABA 2: NOTÍCIAS E EVENTOS ---
# ==========================================
with tab_noticias:
    sub_tab_nova, sub_tab_gerenciar = st.tabs(["➕ Publicar Notícia", "📝 Editar e Gerir Galeria"])

    with sub_tab_nova:
        with st.form("form_nova_noticia", clear_on_submit=True):
            titulo_n = st.text_input("Título da Notícia")
            conteudo_n = st.text_area("Texto / Conteúdo")
            st.write("🖼️ **Adicionar Fotos:**")
            fotos_n = st.file_uploader("Escolha os arquivos", type=['jpg','png','jpeg'], accept_multiple_files=True)
            st.write("🎥 **Adicionar Vídeos:**")
            videos_n = st.text_area("Links do YouTube (Cole um link por linha)")
            
            if st.form_submit_button("Publicar Notícia"):
                galeria_completa = []
                # Processa Fotos
                if fotos_n:
                    with st.spinner("Subindo imagens..."):
                        for f in fotos_n:
                            res_u = fazer_upload_imagem(f)
                            if res_u: galeria_completa.append(res_u)
                # Processa Vídeos
                if videos_n:
                    links_v = [v.strip() for v in videos_n.replace('\n', ',').split(',') if v.strip()]
                    galeria_completa.extend(links_v)
                
                if titulo_n and conteudo_n and galeria_completa:
                    supabase.table("noticias_eventos").insert({
                        "titulo": titulo_n, "conteudo": conteudo_n, 
                        "tipo_midia": "misto", "url_midia": ",".join(galeria_completa)
                    }).execute()
                    st.success("Notícia publicada com sucesso!")
                    st.rerun()
                else:
                    st.error("Preencha o título, conteúdo e adicione pelo menos uma mídia.")

    with sub_tab_gerenciar:
        noticias = supabase.table("noticias_eventos").select("*").order("data_publicacao", desc=True).execute().data
        for n in noticias:
            with st.expander(f"📅 {n['data_publicacao'][:10]} - Editar: {n['titulo']}"):
                edit_t = st.text_input("Título", value=n['titulo'], key=f"et_{n['id']}")
                edit_c = st.text_area("Conteúdo", value=n['conteudo'], key=f"ec_{n['id']}")
                
                # GERENCIAR MÍDIAS ATUAIS
                if n['url_midia']:
                    midias_atuais = [m.strip() for m in n['url_midia'].split(",") if m.strip()]
                    st.write("🖼️ **Galeria Atual (Clique para remover itens):**")
                    cols_m = st.columns(5)
                    for i, url in enumerate(midias_atuais):
                        with cols_m[i % 5]:
                            if "youtube.com" in url or "youtu.be" in url:
                                st.code("🎥 Vídeo YouTube")
                            else:
                                st.image(url, width=100)
                            if st.button("🗑️ Remover", key=f"rm_m_{n['id']}_{i}"):
                                midias_atuais.remove(url)
                                supabase.table("noticias_eventos").update({"url_midia": ",".join(midias_atuais)}).eq("id", n['id']).execute()
                                st.rerun()
                    
                    st.write("---")
                    st.write("➕ **Adicionar mais à esta notícia:**")
                    c_mais1, c_mais2 = st.columns(2)
                    m_fotos = c_mais1.file_uploader("Subir mais fotos", type=['jpg','png'], accept_multiple_files=True, key=f"mf_{n['id']}")
                    m_videos = c_mais2.text_area("Mais links de vídeo", key=f"mv_{n['id']}")
                    
                    if st.button("💾 Atualizar Galeria e Textos", key=f"bup_{n['id']}"):
                        novos_links = []
                        if m_fotos:
                            for f in m_fotos:
                                res_l = fazer_upload_imagem(f)
                                if res_l: novos_links.append(res_l)
                        if m_videos:
                            novos_links.extend([v.strip() for v in m_videos.replace('\n', ',').split(',') if v.strip()])
                        
                        galeria_final = ",".join(midias_atuais + novos_links)
                        supabase.table("noticias_eventos").update({
                            "titulo": edit_t, "conteudo": edit_c, "url_midia": galeria_final
                        }).eq("id", n['id']).execute()
                        st.success("Notícia atualizada!")
                        st.rerun()

                if st.button("🗑️ EXCLUIR NOTÍCIA COMPLETA", key=f"del_not_{n['id']}"):
                    supabase.table("noticias_eventos").delete().eq("id", n['id']).execute()
                    st.rerun()

# ==========================================
# --- ABA 3: ESCALA DE MISSAS ---
# ==========================================
with tab_missas:
    sub_m_n, sub_m_g = st.tabs(["➕ Novo Horário", "📝 Gerenciar Escala"])
    
    with sub_m_n:
        with st.form("form_nova_missa", clear_on_submit=True):
            col_m1, col_m2 = st.columns(2)
            mn_parq = col_m1.text_input("Paróquia/Capela")
            mn_dia = col_m1.selectbox("Dia", ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"])
            mn_hora = col_m2.time_input("Horário", value=datetime.strptime("19:00", "%H:%M").time())
            mn_padre = col_m2.text_input("Padre Responsável")
            mn_obs = st.text_area("Observação / Aviso Especial")
            
            if st.form_submit_button("Salvar Horário"):
                if mn_parq:
                    supabase.table("escala_missas").insert({
                        "paroquia": mn_parq, "dia_semana": mn_dia, "horario": mn_hora.strftime("%H:%M:%S"),
                        "nome_padre": mn_padre, "observacao": mn_obs
                    }).execute()
                    st.success("Cadastrado!")
                    st.rerun()

    with sub_m_g:
        missas_lista = supabase.table("escala_missas").select("*").order("paroquia").execute().data
        for m in missas_lista:
            with st.expander(f"📍 {m['paroquia']} - {m['dia_semana']}"):
                with st.form(f"f_edit_m_{m['id']}"):
                    me_p = st.text_input("Paróquia", value=m['paroquia'])
                    me_d = st.selectbox("Dia", ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"], 
                                       index=["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"].index(m['dia_semana']))
                    me_h = st.time_input("Horário", value=datetime.strptime(m['horario'], "%H:%M:%S").time())
                    me_pad = st.text_input("Padre", value=m['nome_padre'] or "")
                    me_obs = st.text_area("Aviso", value=m['observacao'] or "")
                    
                    if st.form_submit_button("Salvar Alterações"):
                        supabase.table("escala_missas").update({
                            "paroquia": me_p, "dia_semana": me_d, "horario": me_h.strftime("%H:%M:%S"),
                            "nome_padre": me_pad, "observacao": me_obs
                        }).eq("id", m['id']).execute()
                        st.rerun()
                if st.button("🗑️ Excluir Horário", key=f"excl_m_{m['id']}"):
                    supabase.table("escala_missas").delete().eq("id", m['id']).execute()
                    st.rerun()

# --- ABA 4: INSTITUCIONAL (QUEM SOMOS) ---
with tab_inst:
    st.header("🏠 Informações da Igreja")
    
    # 1. Busca os dados atuais
    res_inst = supabase.table("institucional").select("*").limit(1).execute().data
    
    if res_inst:
        atual = res_inst[0]
        with st.form("form_institucional_completo"):
            st.subheader("Editar Informações")
            novo_texto = st.text_area("História / Quem Somos", value=atual['texto_quem_somos'], height=250)
            
            st.write("🖼️ **Foto da Fachada:**")
            if atual['url_foto_igreja']:
                st.image(atual['url_foto_igreja'], width=300, caption="Foto atual no site")
            
            arquivo_foto = st.file_uploader("Escolha uma nova foto para trocar", type=['jpg', 'png', 'jpeg'])
            
            # Botão de Salvar
            if st.form_submit_button("💾 Salvar Alterações Institucionais"):
                # Por padrão, mantém a URL que já existe
                url_para_salvar = atual['url_foto_igreja']
                
                # Se o usuário escolheu um novo arquivo, faz o upload e pega a nova URL
                if arquivo_foto:
                    with st.spinner("Otimizando e subindo nova imagem..."):
                        nova_url = fazer_upload_imagem(arquivo_foto)
                        if nova_url:
                            url_para_salvar = nova_url
                
                # AGORA SALVA NO SUPABASE (Texto + URL)
                try:
                    supabase.table("institucional").update({
                        "texto_quem_somos": novo_texto,
                        "url_foto_igreja": url_para_salvar
                    }).eq("id", atual['id']).execute()
                    
                    st.success("Tudo pronto! As informações foram atualizadas.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar no banco: {e}")
    else:
        # Caso o banco esteja vazio (primeira vez)
        st.info("Ainda não há dados. Crie o primeiro conteúdo abaixo:")
        with st.form("form_inst_primeiro"):
            t_novo = st.text_area("Texto Quem Somos")
            f_nova = st.file_uploader("Foto da Igreja", type=['jpg', 'png'])
            if st.form_submit_button("Criar Página"):
                url_n = fazer_upload_imagem(f_nova) if f_nova else ""
                supabase.table("institucional").insert({
                    "texto_quem_somos": t_novo, 
                    "url_foto_igreja": url_n
                }).execute()
                st.rerun()
# ==========================================
# --- ABA 5: EQUIPE (Mestre apenas) ---
# ==========================================
if st.session_state.usuario['role'] == 'mestre':
    with tab_equipe[0]:
        st.header("👥 Gestão de Equipe")
        with st.form("form_novo_usuario"):
            u_email = st.text_input("E-mail da nova coordenadora")
            if st.form_submit_button("Cadastrar (Senha Inicial: 123456)"):
                hash_init = gerar_senha_criptografada("123456")
                supabase.table("usuarios_coordenacao").insert({
                    "email": u_email, "senha": hash_init, "role": "padrao"
                }).execute()
                st.success("Cadastrada!")
                st.rerun()
        
        st.write("---")
        lista_equipe = supabase.table("usuarios_coordenacao").select("*").execute().data
        for user in lista_equipe:
            if user['id'] != st.session_state.usuario['id']:
                c_u1, c_u2 = st.columns([3, 1])
                c_u1.write(f"📧 **{user['email']}** ({user['role']})")
                if c_u2.button("Resetar Senha", key=f"rs_u_{user['id']}"):
                    h_reset = gerar_senha_criptografada("123456")
                    supabase.table("usuarios_coordenacao").update({"senha": h_reset}).eq("id", user['id']).execute()
                    st.info("Senha resetada para 123456")