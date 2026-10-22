"""
Página: detecção de plantas daninhas em imagens de drone (estudo de caso agronômico).
Fica dentro da pasta pages/, ao lado de Como_funciona.py. Usa as mesmas bibliotecas
do app.py (numpy + OpenCV), sem PyTorch nem GPU.

Pipeline:
  1. Imagem aérea (lavoura simulada ou foto real enviada)
  2. Índice de vegetação ExG + limiar de Otsu  -> o que é planta e o que é solo
  3. Detecção das linhas de plantio            -> onde a cultura deveria estar
  4. Planta fora da linha = planta daninha     -> manchas detectadas
  5. Grade de aplicação                        -> mapa de prescrição e economia de herbicida
"""

import numpy as np
import cv2
import streamlit as st

st.set_page_config(page_title="Plantas daninhas por drone — demo", page_icon="🌱", layout="wide")

COR_CULTURA = (40, 190, 90)
COR_DANINHA = (235, 45, 45)
COR_LINHA = (255, 230, 80)


# ---------------- 1. Lavoura simulada ----------------

def gerar_lavoura(largura, altura, gsd_cm, espac_cm, angulo, n_reboleiras, por_reboleira,
                  iluminacao_irregular, seed):
    """Desenha uma lavoura de soja vista de cima e devolve (imagem RGB, gabarito das daninhas)."""
    rng = np.random.default_rng(seed)
    H, W = altura, largura

    # Solo: cor de terra, manchas suaves de umidade e textura fina
    base = np.array([150, 112, 80], dtype=np.float32)
    manchas = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 30)
    manchas /= np.abs(manchas).max() + 1e-6
    img = base + manchas[..., None] * 20 + rng.normal(0, 6, (H, W, 3)).astype(np.float32)
    for _ in range(int(H * W / 900)):  # torrões e palha
        x, y = int(rng.integers(0, W)), int(rng.integers(0, H))
        tom = float(rng.uniform(-35, 30))
        cv2.circle(img, (x, y), int(rng.integers(1, 3)), (150 + tom, 112 + tom, 80 + tom * 0.8), -1)

    # Cultura: plantas de soja ao longo de linhas paralelas inclinadas
    espac_px = espac_cm / gsd_cm
    passo_planta = 7.0 / gsd_cm                        # ~14 plantas por metro
    tg = np.tan(np.radians(angulo))
    passo_x = espac_px / np.cos(np.radians(angulo))    # espaçamento medido na perpendicular
    alcance = abs(tg) * H + passo_x
    for x0 in np.arange(-alcance, W + alcance, passo_x):
        for y in np.arange(rng.uniform(0, passo_planta), H, passo_planta * np.cos(np.radians(angulo))):
            x = x0 + (y - H / 2) * tg
            if not (-10 < x < W + 10) or rng.random() < 0.05:   # 5% de falhas na linha
                continue
            cx, cy = x + rng.normal(0, 0.6 / gsd_cm), y
            verde = np.array([62, 138, 50]) + rng.normal(0, 10, 3)
            giro = rng.uniform(0, 360)
            for k in range(3):                               # folha trifoliolada
                a = np.radians(giro + 120 * k)
                fx, fy = cx + np.cos(a) * 4.5 / gsd_cm, cy + np.sin(a) * 4.5 / gsd_cm
                cv2.ellipse(img, (int(fx), int(fy)), (int(5.5 / gsd_cm), int(3.5 / gsd_cm)),
                            np.degrees(a), 0, 360, tuple(float(c) for c in verde), -1, cv2.LINE_AA)

    # Plantas daninhas: em reboleiras (manchas) e algumas isoladas
    gabarito = np.zeros((H, W), dtype=np.uint8)
    posicoes = []
    for _ in range(n_reboleiras):
        cx, cy = rng.uniform(0, W), rng.uniform(0, H)
        dispersao = rng.uniform(25, 60) / gsd_cm
        posicoes += [(cx + rng.normal(0, dispersao), cy + rng.normal(0, dispersao))
                     for _ in range(por_reboleira)]
    posicoes += [(rng.uniform(0, W), rng.uniform(0, H)) for _ in range(n_reboleiras * 2)]

    for (x, y) in posicoes:
        if not (0 <= x < W and 0 <= y < H):
            continue
        x, y = int(x), int(y)
        if rng.random() < 0.5:   # gramínea: folhas finas em tufo
            cor = tuple(float(c) for c in np.array([112, 152, 58]) + rng.normal(0, 8, 3))
            for _ in range(int(rng.integers(5, 9))):
                a = rng.uniform(0, 2 * np.pi)
                comp = rng.uniform(6, 13) / gsd_cm
                p2 = (int(x + np.cos(a) * comp), int(y + np.sin(a) * comp))
                for alvo, valor in ((img, cor), (gabarito, 255)):
                    cv2.line(alvo, (x, y), p2, valor, max(2, int(2.5 / gsd_cm)), cv2.LINE_AA)
        else:                    # folha larga: folhas arredondadas
            cor = tuple(float(c) for c in np.array([58, 120, 42]) + rng.normal(0, 8, 3))
            for _ in range(int(rng.integers(2, 5))):
                px = int(x + rng.normal(0, 3 / gsd_cm))
                py = int(y + rng.normal(0, 3 / gsd_cm))
                r = int(rng.uniform(3, 6.5) / gsd_cm)
                for alvo, valor in ((img, cor), (gabarito, 255)):
                    cv2.circle(alvo, (px, py), r, valor, -1, cv2.LINE_AA)

    if iluminacao_irregular:  # sol de lado + sombra de nuvem
        gx = np.linspace(0.72, 1.15, W, dtype=np.float32)[None, :]
        nuvem = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 90)
        nuvem = 1 - 0.25 * np.clip(nuvem / (np.abs(nuvem).max() + 1e-6), 0, 1)
        img *= (gx * nuvem)[..., None]

    return np.clip(img, 0, 255).astype(np.uint8), gabarito > 127


# ---------------- 2. Vegetação: índice ExG + Otsu ----------------

def indice_exg(img):
    """Excess Green: 2g - r - b, com as cores normalizadas pela soma (resiste a sombra e brilho)."""
    f = img.astype(np.float32)
    soma = f.sum(axis=2) + 1e-6
    r, g, b = f[..., 0] / soma, f[..., 1] / soma, f[..., 2] / soma
    return 2 * g - r - b


def segmentar_vegetacao(exg):
    lo, hi = np.percentile(exg, 1), np.percentile(exg, 99.5)
    u8 = np.clip((exg - lo) / (hi - lo + 1e-6) * 255, 0, 255).astype(np.uint8)
    t, _ = cv2.threshold(u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    limiar_exg = max(lo + t / 255 * (hi - lo), 0.03)   # nunca chama de planta algo quase cinza
    veg = (exg > limiar_exg).astype(np.uint8)
    veg = cv2.morphologyEx(veg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return veg > 0, limiar_exg


# ---------------- 3. Linhas de plantio ----------------

def matriz_rotacao(h, w, angulo):
    """Rotação com tela ampliada, para nada da imagem ficar de fora."""
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angulo, 1.0)
    c, s = abs(M[0, 0]), abs(M[0, 1])
    nw, nh = int(h * s + w * c), int(h * c + w * s)
    M[0, 2] += nw / 2 - w / 2
    M[1, 2] += nh / 2 - h / 2
    return M, (nw, nh)


def perfil_colunas(mascara, angulo):
    h, w = mascara.shape
    M, tam = matriz_rotacao(h, w, angulo)
    rot = cv2.warpAffine(mascara.astype(np.float32), M, tam, flags=cv2.INTER_NEAREST)
    val = cv2.warpAffine(np.ones((h, w), np.float32), M, tam, flags=cv2.INTER_NEAREST)
    n = val.sum(axis=0)
    ok = n >= max(15, 0.05 * n.max())   # ignora só as colunas quase vazias dos cantos
    perfil = np.where(ok, rot.sum(axis=0) / np.maximum(n, 1), 0)
    return perfil, ok, M, tam


def estimar_angulo(veg):
    """Testa ângulos e fica com o que deixa as linhas 'em pé': o perfil de colunas mais contrastado."""
    escala = 300 / max(veg.shape)
    peq = cv2.resize(veg.astype(np.uint8), None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA)

    def nota(a):
        p, ok, _, _ = perfil_colunas(peq, a)
        return p[ok].var()

    grossos = np.arange(-90, 90, 2.0)
    melhor = grossos[np.argmax([nota(a) for a in grossos])]
    finos = np.arange(melhor - 2, melhor + 2.01, 0.25)
    return float(finos[np.argmax([nota(a) for a in finos])])


def detectar_linhas(veg, angulo, espac_px, meia_faixa_px):
    h, w = veg.shape
    perfil, ok, M, (nw, nh) = perfil_colunas(veg, angulo)
    k = max(3, int(espac_px / 4) | 1)
    suave = np.convolve(perfil, np.ones(k) / k, mode="same")
    limiar = suave[ok].mean()
    dist_min = 0.6 * espac_px
    picos = []
    for x in np.argsort(-suave):          # pico mais forte primeiro, sem vizinhos próximos demais
        if suave[x] <= limiar:
            break
        if ok[x] and all(abs(x - p) >= dist_min for p in picos):
            picos.append(int(x))
    picos.sort()

    faixa_rot = np.zeros((nh, nw), np.uint8)
    eixo_rot = np.zeros((nh, nw), np.uint8)
    for p in picos:
        faixa_rot[:, max(0, p - meia_faixa_px): p + meia_faixa_px + 1] = 1
        eixo_rot[:, max(0, p - 1): p + 1] = 1
    Minv = cv2.invertAffineTransform(M)
    faixa = cv2.warpAffine(faixa_rot, Minv, (w, h), flags=cv2.INTER_NEAREST) > 0
    eixo = cv2.warpAffine(eixo_rot, Minv, (w, h), flags=cv2.INTER_NEAREST) > 0
    return faixa, eixo, len(picos)


# ---------------- 4 e 5. Daninhas e prescrição ----------------

def separar_daninhas(veg, faixa, area_min_px):
    candidatas = (veg & ~faixa).astype(np.uint8)
    n, rotulos, stats, _ = cv2.connectedComponentsWithStats(candidatas, connectivity=8)
    manter = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= area_min_px]
    daninha = np.isin(rotulos, manter)
    caixas = [tuple(stats[i, :4]) for i in manter]
    return daninha, caixas


def grade_prescricao(mascara, celula_px):
    h, w = mascara.shape
    linhas, colunas = int(np.ceil(h / celula_px)), int(np.ceil(w / celula_px))
    grade = np.zeros((linhas, colunas), bool)
    for i in range(linhas):
        for j in range(colunas):
            grade[i, j] = mascara[i * celula_px:(i + 1) * celula_px, j * celula_px:(j + 1) * celula_px].any()
    return grade


def misturar(img, mascara, cor, alfa):
    saida = img.astype(np.float32).copy()
    saida[mascara] = saida[mascara] * (1 - alfa) + np.array(cor, np.float32) * alfa
    return saida.astype(np.uint8)


def desenhar_classificacao(img, veg, faixa, daninha, eixo, caixas):
    saida = misturar(img, veg & faixa, COR_CULTURA, 0.55)
    saida = misturar(saida, daninha, COR_DANINHA, 0.75)
    saida[eixo] = COR_LINHA
    esp = max(2, img.shape[1] // 450)
    for (x, y, w, h) in caixas:
        cv2.rectangle(saida, (int(x) - 2, int(y) - 2), (int(x + w) + 2, int(y + h) + 2), COR_DANINHA, esp)
    return saida


def desenhar_prescricao(img, grade, celula_px):
    cinza = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
    saida = (cinza * 0.75).astype(np.uint8)
    h, w = img.shape[:2]
    camada = saida.copy()
    for i, j in zip(*np.nonzero(grade)):
        cv2.rectangle(camada, (j * celula_px, i * celula_px),
                      (min(w, (j + 1) * celula_px) - 1, min(h, (i + 1) * celula_px) - 1), COR_DANINHA, -1)
    saida = cv2.addWeighted(camada, 0.55, saida, 0.45, 0)
    for x in range(0, w, celula_px):
        cv2.line(saida, (x, 0), (x, h), (235, 235, 235), 1)
    for y in range(0, h, celula_px):
        cv2.line(saida, (0, y), (w, y), (235, 235, 235), 1)
    return saida


def colorir_exg(exg):
    lo, hi = np.percentile(exg, 1), np.percentile(exg, 99.5)
    u8 = np.clip((exg - lo) / (hi - lo + 1e-6) * 255, 0, 255).astype(np.uint8)
    return cv2.cvtColor(cv2.applyColorMap(u8, cv2.COLORMAP_VIRIDIS), cv2.COLOR_BGR2RGB)


# ---------------- Interface ----------------

st.title("🌱 Plantas daninhas em imagens de drone")
st.caption("O mesmo raciocínio do futebol, agora na lavoura: detectar o que está fora do lugar "
           "e transformar a imagem em um mapa de aplicação de herbicida.")
st.page_link("app.py", label="Voltar ao estudo de caso do futebol", icon="⚽")

with st.sidebar:
    st.header("Imagem")
    fonte = st.radio("Fonte", ["Lavoura simulada", "Minha foto de drone"])

    if fonte == "Lavoura simulada":
        angulo_sim = st.slider("Inclinação das linhas (°)", 0, 45, 12)
        n_reboleiras = st.slider("Reboleiras de daninhas", 0, 12, 5)
        por_reboleira = st.slider("Daninhas por reboleira", 5, 40, 18)
        ilum = st.checkbox("Iluminação irregular (sol de lado, nuvem)", value=True)
        seed = st.number_input("Seed", value=7, step=1)
        gsd_cm = 1.0
    else:
        arquivo = st.file_uploader("Foto vertical (nadir) de lavoura em linhas", type=["jpg", "jpeg", "png"])
        gsd_cm = st.number_input("Resolução da foto, GSD (cm/pixel)", 0.1, 10.0, 0.8, step=0.1,
                                 help="Depende da altura de voo e da câmera. "
                                      "Ex.: DJI Phantom 4 Pro a 30 m ≈ 0,8 cm/pixel.")

    st.header("Processamento")
    espac_cm = st.slider("Espaçamento entre linhas (cm)", 30, 100, 50, step=5,
                         help="Soja: 40–50 cm. Milho: 45–90 cm.")
    faixa_cm = st.slider("Largura da faixa da cultura (cm)", 8, 40, 20, step=2,
                         help="Tudo que é verde dentro desta faixa conta como cultura.")
    area_min_cm2 = st.slider("Área mínima de uma mancha (cm²)", 5, 200, 20, step=5)
    celula_m = st.slider("Célula de aplicação (m)", 0.5, 3.0, 1.0, step=0.5,
                         help="Menor área que o pulverizador consegue ligar ou desligar.")

# --- 1. Imagem ---
gabarito = None
if fonte == "Lavoura simulada":
    img, gabarito = gerar_lavoura(960, 640, gsd_cm, espac_cm, angulo_sim, n_reboleiras,
                                  por_reboleira, ilum, int(seed))
else:
    if arquivo is None:
        st.info("Envie uma foto aérea vertical de uma lavoura em linhas (soja, milho, feijão…). "
                "Funciona melhor com a cultura ainda pequena, antes de as linhas se fecharem.")
        st.stop()
    bruto = cv2.imdecode(np.frombuffer(arquivo.read(), np.uint8), cv2.IMREAD_COLOR)
    if bruto is None:
        st.error("Não consegui abrir essa imagem.")
        st.stop()
    img = cv2.cvtColor(bruto, cv2.COLOR_BGR2RGB)
    escala = min(1.0, 1400 / max(img.shape[:2]))
    if escala < 1:
        img = cv2.resize(img, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA)
        gsd_cm = gsd_cm / escala   # cada pixel reduzido cobre mais chão

# --- 2 a 5. Pipeline ---
exg = indice_exg(img)
veg, limiar_exg = segmentar_vegetacao(exg)
angulo = estimar_angulo(veg)
espac_px = espac_cm / gsd_cm
faixa, eixo, n_linhas = detectar_linhas(veg, angulo, espac_px, int(faixa_cm / gsd_cm / 2))
daninha, caixas = separar_daninhas(veg, faixa, area_min_cm2 / gsd_cm ** 2)
celula_px = max(4, int(round(celula_m * 100 / gsd_cm)))
grade = grade_prescricao(daninha, celula_px)

h, w = img.shape[:2]
area_m2 = h * w * (gsd_cm / 100) ** 2
economia = 1 - grade.mean() if grade.size else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Área da imagem", f"{area_m2:,.0f} m²".replace(",", "."))
c2.metric("Linhas de plantio", n_linhas, help=f"Ângulo estimado: {angulo:.1f}°")
c3.metric("Manchas de daninha", len(caixas))
c4.metric("Economia de herbicida", f"{economia:.0%}",
          help="Fração da área que NÃO precisa ser pulverizada, comparada à aplicação em área total.")

if n_linhas < 2:
    st.warning("Encontrei menos de duas linhas de plantio. Confira o GSD e o espaçamento: "
               "se estiverem errados, o app procura linhas no tamanho errado.")

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("1. Foto aérea")
    st.image(img, width="stretch")
    st.subheader("3. Cultura × daninha")
    st.image(desenhar_classificacao(img, veg, faixa, daninha, eixo, caixas), width="stretch")
    st.caption("Verde: planta dentro da faixa da linha (cultura). Vermelho: planta fora dela "
               "(daninha). Amarelo: eixo das linhas encontradas.")
with col_b:
    st.subheader("2. Índice de verde (ExG)")
    st.image(colorir_exg(exg), width="stretch")
    st.caption(f"Amarelo = mais verde. Acima de ExG {limiar_exg:.2f} (limiar de Otsu) o pixel é planta.")
    st.subheader("4. Mapa de prescrição")
    st.image(desenhar_prescricao(img, grade, celula_px), width="stretch")
    st.caption(f"Células de {celula_m:g} m × {celula_m:g} m. Vermelho = pulverizar "
               f"({grade.sum()} de {grade.size} células).")

# --- Conferência com o gabarito (só na simulação) ---
if gabarito is not None:
    st.divider()
    st.subheader("Conferência com o gabarito")
    acertos = (daninha & gabarito).sum()
    recall = acertos / max(1, gabarito.sum())
    precisao = acertos / max(1, daninha.sum())
    na_linha = (gabarito & faixa).sum() / max(1, gabarito.sum())
    grade_real = grade_prescricao(gabarito, celula_px)
    escapes = int((grade_real & ~grade).sum())

    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Daninha encontrada (recall)", f"{recall:.0%}")
    g2.metric("Acerto do que foi marcado (precisão)", f"{precisao:.0%}")
    g3.metric("Daninha escondida na linha", f"{na_linha:.0%}",
              help="Parte da daninha que cresce dentro da faixa da cultura: este método não a vê.")
    g4.metric("Células com daninha sem aplicação", escapes,
              help="Escapes: células que tinham daninha de verdade mas ficaram fora do mapa.")
    st.caption("A daninha que nasce dentro da linha tem a mesma cor da soja e fica no mesmo lugar: "
               "por cor e posição ela é invisível. É aí que entra uma rede treinada (YOLOv8, CNN), "
               "que aprende o formato da folha.")

with st.expander("Como funciona, em 5 etapas"):
    st.markdown(f"""
1. **Imagem.** Um drone voa a baixa altura e fotografa a lavoura de cima. Cada pixel cobre
   {gsd_cm:.1f} cm de chão (o GSD).
2. **O que é planta.** O índice *Excess Green* (ExG = 2g − r − b) realça o verde e apaga solo e palha.
   Como as cores são divididas pela soma R+G+B, sombra e sol forte quase não mudam o resultado.
   O limiar de Otsu escolhe sozinho o corte entre planta e solo.
3. **Onde a cultura deveria estar.** O app gira a máscara até as linhas ficarem em pé e soma o verde
   de cada coluna: as linhas viram picos regulares, a cada {espac_cm} cm.
4. **Daninha = planta fora do lugar.** Tudo que é verde e está fora da faixa da linha vira candidata;
   manchas menores que {area_min_cm2} cm² são descartadas como ruído.
5. **Prescrição.** O talhão é dividido em células do tamanho que o pulverizador consegue controlar.
   Só as células com daninha recebem herbicida.
""")
    st.markdown("**Trocar por um modelo treinado:** anote recortes no CVAT (soja, folha larga, "
                "gramínea), treine com `YOLO('yolov8n.pt').train(data='daninhas.yaml')` e troque as "
                "etapas 2 a 4 por `model.predict('ortomosaico.jpg')`. As caixas detectadas entram na "
                "mesma grade da etapa 5.")
