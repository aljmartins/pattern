"""
App Streamlit — demonstração interativa do pipeline (etapas 04/05)

Rodar localmente:
    pip install -r requirements.txt
    streamlit run app.py

Publicar grátis (Streamlit Community Cloud):
    1. Suba este arquivo + requirements.txt num repositório no GitHub
    2. Entre em https://share.streamlit.io, conecte o repositório
    3. Aponte o "main file path" para app.py -> Deploy
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Rastreamento + estatística — demo", page_icon="⚽", layout="wide")

CAMPO_M = (105, 68)
ESCALA_PX_POR_M = 8
CAMPO_PX = (CAMPO_M[0] * ESCALA_PX_POR_M, CAMPO_M[1] * ESCALA_PX_POR_M)
DIST_MAX_ASSOCIACAO_PX = 4.0 * ESCALA_PX_POR_M
CORES = [(201, 129, 46), (46, 122, 201), (201, 46, 98), (46, 201, 153), (160, 90, 201), (201, 201, 46)]


def gerar_trajetoria_real(n_quadros, campo_m, seed_offset):
    r = np.random.default_rng(seed=seed_offset)
    cx, cy = r.uniform(10, campo_m[0]-10), r.uniform(5, campo_m[1]-5)
    vx, vy = r.uniform(-0.4, 0.4), r.uniform(-0.3, 0.3)
    pos = []
    for _ in range(n_quadros):
        vx = np.clip(vx + r.normal(0, 0.08), -1.8, 1.8)
        vy = np.clip(vy + r.normal(0, 0.08), -1.8, 1.8)
        cx = np.clip(cx + vx, 2, campo_m[0]-2)
        cy = np.clip(cy + vy, 2, campo_m[1]-2)
        pos.append((cx, cy))
    return np.array(pos)


class RastreadorSimples:
    def __init__(self):
        self.proximo_id = 0
        self.posicao_atual = {}
        self.trajetorias = {}
        self.distancia_m = {}

    def atualizar(self, deteccoes):
        ids_usados = set()
        for (x, y) in deteccoes:
            melhor_id, melhor_dist = None, DIST_MAX_ASSOCIACAO_PX
            for tid, (px, py) in self.posicao_atual.items():
                if tid in ids_usados:
                    continue
                d = np.hypot(x - px, y - py)
                if d < melhor_dist:
                    melhor_id, melhor_dist = tid, d
            if melhor_id is None:
                melhor_id = self.proximo_id
                self.proximo_id += 1
                self.trajetorias[melhor_id] = []
                self.distancia_m[melhor_id] = 0.0
            else:
                px, py = self.posicao_atual[melhor_id]
                self.distancia_m[melhor_id] += np.hypot(x - px, y - py) / ESCALA_PX_POR_M
            self.posicao_atual[melhor_id] = (x, y)
            self.trajetorias[melhor_id].append((x, y))
            ids_usados.add(melhor_id)
        return ids_usados


def rodar_simulacao(n_jogadores, n_quadros, prob_falha, seed):
    rng = np.random.default_rng(seed=seed)
    trajetorias_reais = [gerar_trajetoria_real(n_quadros, CAMPO_M, seed_offset=100 + i)
                         for i in range(n_jogadores)]

    def detector_simulado(quadro_idx):
        deteccoes = []
        for traj in trajetorias_reais:
            if rng.random() < prob_falha:
                continue
            x_m, y_m = traj[quadro_idx]
            ruido = rng.normal(0, 0.15, size=2)
            deteccoes.append(((x_m + ruido[0]) * ESCALA_PX_POR_M, (y_m + ruido[1]) * ESCALA_PX_POR_M))
        rng.shuffle(deteccoes)
        return deteccoes

    rastreador = RastreadorSimples()
    for q in range(n_quadros):
        rastreador.atualizar(detector_simulado(q))
    return rastreador


def desenhar_campo(rastreador):
    img = np.full((CAMPO_PX[1], CAMPO_PX[0], 3), (60, 122, 79), dtype=np.uint8)
    branco = (235, 240, 236)
    cv2.rectangle(img, (4, 4), (CAMPO_PX[0]-4, CAMPO_PX[1]-4), branco, 2)
    cv2.line(img, (CAMPO_PX[0]//2, 0), (CAMPO_PX[0]//2, CAMPO_PX[1]), branco, 2)
    cv2.circle(img, (CAMPO_PX[0]//2, CAMPO_PX[1]//2), int(9.15*ESCALA_PX_POR_M), branco, 2)
    for tid, pontos in rastreador.trajetorias.items():
        cor = CORES[tid % len(CORES)]
        pts = np.array(pontos, dtype=np.int32)
        for i in range(1, len(pts)):
            cv2.line(img, tuple(pts[i-1]), tuple(pts[i]), cor, 2, cv2.LINE_AA)
        cv2.circle(img, tuple(pts[-1]), 6, cor, -1)
        cv2.putText(img, str(tid), (pts[-1][0]+8, pts[-1][1]+4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


# ---------------- Interface ----------------

st.title("⚽ Rastreamento + estatística — pipeline simulado")
st.caption("Etapas 04/05 do infográfico, rodando ao vivo. Troque os parâmetros na barra lateral.")

with st.sidebar:
    st.header("Parâmetros da simulação")
    n_jogadores = st.slider("Nº de jogadores", 2, 6, 5)
    n_quadros = st.slider("Quadros simulados (~10/seg)", 50, 300, 150, step=10)
    prob_falha = st.slider("Probabilidade de falha de detecção", 0.0, 0.3, 0.06, step=0.01)
    seed = st.number_input("Seed", value=7, step=1)

rastreador = rodar_simulacao(n_jogadores, n_quadros, prob_falha, seed)

col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("Trajetórias reconstruídas")
    st.image(desenhar_campo(rastreador), use_container_width="stretch")

with col2:
    st.subheader("Distância por track")
    ids_validos = [tid for tid in rastreador.distancia_m
                   if len(rastreador.trajetorias[tid]) > n_quadros * 0.3]
    ids_validos.sort(key=lambda tid: -rastreador.distancia_m[tid])
    valores_km = [rastreador.distancia_m[tid]/1000 for tid in ids_validos]

    fig, ax = plt.subplots(figsize=(5, 3.5))
    barras = ax.bar([f"track {tid}" for tid in ids_validos], valores_km, color="#C9812E")
    ax.set_ylabel("km percorridos")
    for b, v in zip(barras, valores_km):
        ax.text(b.get_x()+b.get_width()/2, v, f"{v:.3f}", ha="center", va="bottom", fontsize=8)
    st.pyplot(fig)

    st.metric("Tracks criados", rastreador.proximo_id,
               help=f"Esperado perto de {n_jogadores}; valores maiores indicam fragmentação de identidade")

st.divider()
st.caption("Trocar para vídeo real: substitua `rodar_simulacao()` por uma chamada a "
           "`model.track(source='partida.mp4', stream=True, persist=True)` do YOLOv8 — "
           "o rastreador e as métricas continuam os mesmos.")
