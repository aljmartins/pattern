"""
Página de explicação do app (aparece no menu lateral como "Como funciona").
Fica dentro da pasta pages/, ao lado do app.py.
"""

import streamlit as st

st.set_page_config(page_title="Como funciona — rastreamento", page_icon="📖", layout="centered")

st.page_link("app.py", label="Voltar para a simulação", icon="⚽")

# Pontos do diagrama: (x, y, detecção perdida?)
PONTOS = [(50, 137, False), (75, 124, False), (104, 114, False), (130, 112, False),
          (169, 133, False), (208, 120, False), (239, 124, True), (268, 127, False),
          (309, 123, False), (345, 109, False), (373, 100, False), (407, 75, False),
          (433, 69, False), (473, 58, True), (490, 60, False), (515, 54, False),
          (551, 61, False), (574, 68, False), (586, 80, False)]

detectados = [(x, y) for x, y, perdido in PONTOS if not perdido]
linha_track = " ".join(f"{x},{y}" for x, y in detectados)
circulos = "".join(
    f'<circle cx="{x}" cy="{y}" r="5" class="cf-miss"/>' if perdido
    else f'<circle cx="{x}" cy="{y}" r="4" class="cf-det"/>'
    for x, y, perdido in PONTOS
)

HTML = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&display=swap');

.cf {{ font-size: 1.02rem; line-height: 1.6; color: inherit; }}
.cf h1, .cf h2, .cf h3 {{
  font-family: 'Barlow Condensed', 'Arial Narrow', sans-serif;
  letter-spacing: 0.01em; line-height: 1.15; margin: 0;
}}
.cf h2 {{ font-size: 1.75rem; margin: 2.4rem 0 0.9rem; }}
.cf p {{ margin: 0 0 0.9rem; max-width: 68ch; }}
.cf code {{ font-size: 0.9em; padding: 0.1em 0.35em; border-radius: 4px;
           background: rgba(128,128,128,0.16); }}

/* Quadro de abertura: o campo desenhado a giz */
.cf-hero {{
  background: #4F7A3C; color: #EBF0EC; border-radius: 10px;
  padding: 1.6rem 1.6rem 1.1rem; margin-bottom: 0.4rem;
}}
.cf-hero h1 {{ font-size: clamp(2rem, 5vw, 2.8rem); color: #FFFFFF; margin-bottom: 0.5rem; }}
.cf-hero p {{ color: #E1EBDD; margin-bottom: 1.1rem; }}
.cf-hero svg {{ width: 100%; height: auto; display: block; }}
.cf-chalk {{ fill: none; stroke: rgba(235,240,236,0.55); stroke-width: 2; }}
.cf-real {{ fill: none; stroke: rgba(235,240,236,0.7); stroke-width: 2; stroke-dasharray: 3 6; }}
.cf-track {{ fill: none; stroke: #F2A94B; stroke-width: 3; stroke-linejoin: round; }}
.cf-det {{ fill: #FFFFFF; }}
.cf-miss {{ fill: none; stroke: #FFFFFF; stroke-width: 1.5; stroke-dasharray: 2 3; }}
.cf-legend {{ display: flex; flex-wrap: wrap; gap: 0.4rem 1.4rem; font-size: 0.88rem;
              color: #E1EBDD; margin-top: 0.7rem; }}
.cf-legend span {{ display: inline-flex; align-items: center; gap: 0.45rem; }}
.cf-sw {{ display: inline-block; width: 22px; height: 0; border-top: 3px solid #F2A94B; }}
.cf-sw.real {{ border-top: 2px dashed rgba(235,240,236,0.8); }}
.cf-sw.dot {{ width: 8px; height: 8px; border: 0; border-radius: 50%; background: #FFFFFF; }}
.cf-sw.miss {{ width: 9px; height: 9px; border: 1.5px dashed #FFFFFF; border-radius: 50%; }}

/* As quatro etapas, cada uma com a cor de um track do app */
.cf-steps {{ list-style: none; padding: 0; margin: 0; counter-reset: etapa; }}
.cf-steps li {{
  counter-increment: etapa; position: relative;
  padding: 0.2rem 0 0.2rem 3.4rem; margin-bottom: 1.4rem;
}}
.cf-steps li::before {{
  content: counter(etapa); position: absolute; left: 0; top: 0.1rem;
  width: 2.4rem; height: 2.4rem; border-radius: 50%;
  display: grid; place-items: center; color: #FFFFFF;
  font-family: 'Barlow Condensed', 'Arial Narrow', sans-serif; font-size: 1.35rem; font-weight: 700;
  background: var(--cor);
}}
.cf-steps h3 {{ font-size: 1.3rem; margin-bottom: 0.3rem; }}
.cf-steps p {{ margin-bottom: 0.4rem; }}
.cf-steps ul {{ margin: 0.2rem 0 0; padding-left: 1.2rem; }}

.cf-read {{ display: grid; gap: 1rem; }}
.cf-read div {{ border-left: 3px solid rgba(128,128,128,0.4); padding: 0.1rem 0 0.1rem 1rem; }}
.cf-read strong {{ display: block; margin-bottom: 0.15rem; }}

.cf-example {{ border: 1px solid rgba(128,128,128,0.35); border-radius: 10px; padding: 1.1rem 1.3rem; }}
.cf-example .cf-params {{ font-size: 0.92rem; opacity: 0.8; margin-bottom: 0.7rem; }}

.cf-try li {{ margin-bottom: 0.6rem; }}
</style>

<div class="cf">

  <section class="cf-hero">
    <h1>Como o app reconstrói uma partida</h1>
    <p>Uma simulação de ponta a ponta: jogadores inventados correm pelo campo, um detector
    imperfeito tenta enxergá-los e um rastreador precisa descobrir, quadro a quadro, quem é quem.</p>
    <svg viewBox="0 0 640 190" role="img"
         aria-label="Diagrama: o caminho real de um jogador, as detecções ao longo dele, duas detecções perdidas e o track reconstruído">
      <rect x="6" y="6" width="628" height="178" class="cf-chalk"/>
      <line x1="320" y1="6" x2="320" y2="184" class="cf-chalk"/>
      <circle cx="320" cy="95" r="38" class="cf-chalk"/>
      <path d="M40 150 C 140 60, 240 170, 340 110 S 520 40, 600 75" class="cf-real"/>
      <polyline points="{linha_track}" class="cf-track"/>
      {circulos}
    </svg>
    <div class="cf-legend">
      <span><i class="cf-sw real"></i>caminho real do jogador</span>
      <span><i class="cf-sw dot"></i>detecção (com erro)</span>
      <span><i class="cf-sw miss"></i>detecção perdida</span>
      <span><i class="cf-sw"></i>track reconstruído</span>
    </div>
  </section>

  <h2>O caminho dos dados</h2>
  <ol class="cf-steps">
    <li style="--cor:#2E81C9">
      <h3>Os jogadores “de verdade”</h3>
      <p>Para cada jogador, o programa sorteia uma posição inicial num campo de 105 × 68 metros e
      uma velocidade. A cada quadro (cerca de 10 por segundo), a velocidade muda um pouco ao acaso
      e o jogador anda. Esse caminho é o gabarito: o rastreador nunca o vê diretamente.</p>
    </li>
    <li style="--cor:#C9812E">
      <h3>O detector simulado</h3>
      <p>Faz o papel de uma IA de visão, como o YOLO, olhando cada quadro do vídeo. Ele imita os
      defeitos de um detector real:</p>
      <ul>
        <li>adiciona um pequeno erro de posição, de cerca de 15 cm, a cada detecção;</li>
        <li>às vezes não vê um jogador (é a “probabilidade de falha” da barra lateral);</li>
        <li>embaralha a ordem das detecções, porque um detector só diz “há alguém aqui”, nunca quem é.</li>
      </ul>
    </li>
    <li style="--cor:#C92E62">
      <h3>O rastreador</h3>
      <p>É o coração do app. A cada quadro, recebe a lista anônima de detecções e decide a quem
      cada uma pertence, pela regra do vizinho mais próximo: procura o jogador conhecido que estava
      mais perto no quadro anterior. Se ele estiver a menos de 4 metros, a detecção é dele e a
      distância percorrida é somada. Se ninguém estiver perto, o rastreador conclui que é alguém
      novo e cria um novo track, com um novo número.</p>
    </li>
    <li style="--cor:#2E9976">
      <h3>Os resultados na tela</h3>
      <p>O OpenCV desenha o campo com o caminho de cada track, o gráfico mostra quantos quilômetros
      cada um percorreu e o indicador conta quantos tracks foram criados.</p>
    </li>
  </ol>

  <h2>Como ler a tela</h2>
  <div class="cf-read">
    <div><strong>Trajetórias reconstruídas</strong>
      Cada cor é um track, com o número de identificação na ponta. Os pequenos zigue-zagues nas
      linhas são o erro do detector aparecendo no desenho.</div>
    <div><strong>Distância por track</strong>
      Quilômetros percorridos, do track que mais correu para o que menos correu. Tracks presentes
      em menos de 30% dos quadros são descartados como ruído.</div>
    <div><strong>Tracks criados</strong>
      O teste de qualidade. Com 5 jogadores, o ideal são 5 tracks. Se aparecerem 8, o rastreador
      perdeu jogadores no caminho e os recriou com outro número: é a fragmentação de identidade.</div>
  </div>

  <h2>Um exemplo</h2>
  <div class="cf-example">
    <p class="cf-params">3 jogadores, 110 quadros, falha de detecção de 6%, seed 9</p>
    <p>O rastreador criou exatamente 3 tracks, sem fragmentação: com poucas falhas e jogadores
    longe uns dos outros, ninguém se perdeu nem trocou de identidade.</p>
    <p>Cada track percorreu cerca de 60 metros em 11 segundos, perto de 5,5 m/s ou 20 km/h,
    o ritmo de uma corrida forte. Um dos tracks termina encostado na linha lateral: a simulação
    não deixa o jogador sair do campo, então ele fica preso na borda.</p>
  </div>

  <h2>Experimente</h2>
  <ul class="cf-try">
    <li><strong>Falha de detecção em 0,3.</strong> O número de tracks criados passa do número de
    jogadores, mostrando a fragmentação.</li>
    <li><strong>6 jogadores, várias seeds.</strong> Procure uma partida em que dois caminhos se
    cruzam: como o rastreador só olha a distância, ele pode trocar as identidades.</li>
    <li><strong>Mesma seed, outro parâmetro.</strong> A seed fixa o sorteio, então a partida é a
    mesma e só muda o que você alterou. É a forma justa de comparar.</li>
  </ul>

  <h2>Limites e próximo passo</h2>
  <p>Como o erro de 15 cm entra em toda medição, as pequenas oscilações se somam e a distância
  calculada tende a ficar um pouco acima da real. Rastreadores profissionais suavizam isso com
  filtros, como o de Kalman, que também ajudam a prever onde o jogador estará quando um cruzamento
  ou uma falha esconde a detecção.</p>
  <p>Para usar um vídeo de verdade, basta trocar a simulação pelo YOLOv8
  (<code>model.track(source='partida.mp4', stream=True, persist=True)</code>), que detecta os
  jogadores no vídeo. O rastreador e as métricas continuam iguais.</p>

</div>
"""

st.html(HTML)
