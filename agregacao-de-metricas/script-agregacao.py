#!/usr/bin/env python3
"""Exercício didático de funções de agregação de métricas.

O usuário escolhe uma função com -f/--func e informa uma lista de
valores. Cada execução mostra o conceito, o cálculo passo a passo e
o resultado, ajudando a entender como cada agregação funciona.
"""

import argparse
import math
import sys
from collections import Counter


def formatar_numero(valor):
    """Exibe inteiros sem casa decimal e floats com até seis algarismos."""
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, int):
        return str(valor)
    if isinstance(valor, float):
        if math.isnan(valor) or math.isinf(valor):
            return str(valor)
        if valor.is_integer():
            return str(int(valor))
        return f"{valor:.6g}"
    return str(valor)


def formatar_valores(valores):
    return ", ".join(formatar_numero(valor) for valor in valores)


def formatar_resultado(valor):
    if isinstance(valor, dict):
        return "; ".join(
            f"{formatar_numero(chave)} → {formatar_numero(frequencia)}"
            for chave, frequencia in valor.items()
        )
    if isinstance(valor, list):
        if not valor:
            return "(vazio)"
        return ", ".join(formatar_numero(item) for item in valor)
    return formatar_numero(valor)


def exigir_minimo(valores, minimo, nome):
    if len(valores) < minimo:
        raise ValueError(
            f"a função {nome} exige pelo menos {minimo} amostra(s)"
        )


def tempo_decorrido(valores, intervalo):
    if intervalo <= 0:
        raise ValueError("o intervalo entre amostras precisa ser maior que zero")
    return (len(valores) - 1) * intervalo


def aumento_contador(valores):
    total = 0.0
    linhas = []
    for indice in range(1, len(valores)):
        anterior = valores[indice - 1]
        atual = valores[indice]
        if atual >= anterior:
            delta = atual - anterior
            linhas.append(
                f"{formatar_numero(anterior)} → {formatar_numero(atual)}: "
                f"+{formatar_numero(delta)}"
            )
        else:
            delta = atual
            linhas.append(
                f"{formatar_numero(anterior)} → {formatar_numero(atual)}: "
                f"reset detectado, contribuição +{formatar_numero(delta)}"
            )
        total += delta
    return total, linhas


def regressao(valores, intervalo):
    if intervalo <= 0:
        raise ValueError("o intervalo entre amostras precisa ser maior que zero")
    tempos = [indice * intervalo for indice in range(len(valores))]
    media_tempo = math.fsum(tempos) / len(tempos)
    media_valor = math.fsum(valores) / len(valores)
    numerador = math.fsum(
        (tempo - media_tempo) * (valor - media_valor)
        for tempo, valor in zip(tempos, valores)
    )
    denominador = math.fsum((tempo - media_tempo) ** 2 for tempo in tempos)
    inclinacao = numerador / denominador
    intercepto = media_valor - inclinacao * media_tempo
    return inclinacao, intercepto, tempos, media_tempo, media_valor


def count(valores, **opcoes):
    return len(valores), [f"Há {len(valores)} amostra(s) na lista."]


def sum_values(valores, **opcoes):
    total = math.fsum(valores)
    parcelas = " + ".join(formatar_numero(valor) for valor in valores)
    return total, [f"Soma: {parcelas} = {formatar_numero(total)}"]


def avg(valores, **opcoes):
    total = math.fsum(valores)
    media = total / len(valores)
    return media, [
        f"Soma: {formatar_numero(total)}",
        f"Quantidade de amostras: {len(valores)}",
        f"Média: {formatar_numero(total)} / {len(valores)} = "
        f"{formatar_numero(media)}",
    ]


def min_value(valores, **opcoes):
    menor = min(valores)
    return menor, [
        f"Comparando {len(valores)} amostra(s), o menor valor é "
        f"{formatar_numero(menor)}."
    ]


def max_value(valores, **opcoes):
    maior = max(valores)
    return maior, [
        f"Comparando {len(valores)} amostra(s), o maior valor é "
        f"{formatar_numero(maior)}."
    ]


def median(valores, **opcoes):
    ordenados = sorted(valores)
    quantidade = len(ordenados)
    if quantidade % 2 == 1:
        posicao = quantidade // 2
        valor = ordenados[posicao]
        detalhes = [
            f"Valores ordenados: {formatar_valores(ordenados)}",
            f"Quantidade ímpar: o elemento central é o {posicao + 1}º.",
            f"Mediana: {formatar_numero(valor)}",
        ]
        return valor, detalhes

    esquerda = quantidade // 2 - 1
    direita = quantidade // 2
    valor = (ordenados[esquerda] + ordenados[direita]) / 2
    return valor, [
        f"Valores ordenados: {formatar_valores(ordenados)}",
        f"Quantidade par: a mediana é a média dos elementos "
        f"{esquerda + 1}º e {direita + 1}º.",
        f"Cálculo: ({formatar_numero(ordenados[esquerda])} + "
        f"{formatar_numero(ordenados[direita])}) / 2 = "
        f"{formatar_numero(valor)}",
    ]


def mode(valores, **opcoes):
    frequencias = Counter(valores)
    maior_frequencia = max(frequencias.values())
    modas = sorted(
        valor for valor, frequencia in frequencias.items()
        if frequencia == maior_frequencia
    )
    tabela = ", ".join(
        f"{formatar_numero(valor)} → {frequencia}"
        for valor, frequencia in sorted(frequencias.items())
    )
    valor = modas[0] if len(modas) == 1 else modas
    return valor, [
        f"Frequências: {tabela}",
        f"Maior frequência: {maior_frequencia}",
        f"Moda(s): {formatar_valores(modas)}",
    ]


def percentile(valores, p=95.0, **opcoes):
    ordenados = sorted(valores)
    quantidade = len(ordenados)
    if quantidade == 1:
        return ordenados[0], [
            f"Valor ordenado: {formatar_numero(ordenados[0])}",
            "Com uma única amostra, qualquer percentil é esse valor.",
        ]

    posicao = (p / 100) * (quantidade - 1)
    inferior = math.floor(posicao)
    superior = math.ceil(posicao)
    detalhes = [
        f"Valores ordenados: {formatar_valores(ordenados)}",
        f"Posição: ({formatar_numero(p)} / 100) × "
        f"({quantidade} - 1) = {formatar_numero(posicao)}",
    ]

    if inferior == superior:
        valor = ordenados[inferior]
        detalhes.append(
            f"Posição exata: o percentil é o {inferior + 1}º valor, "
            f"{formatar_numero(valor)}."
        )
    else:
        fracao = posicao - inferior
        valor_inferior = ordenados[inferior]
        valor_superior = ordenados[superior]
        valor = valor_inferior + fracao * (valor_superior - valor_inferior)
        detalhes.append(
            f"Interpolação: {formatar_numero(valor_inferior)} + "
            f"{formatar_numero(fracao)} × "
            f"({formatar_numero(valor_superior)} - "
            f"{formatar_numero(valor_inferior)}) = "
            f"{formatar_numero(valor)}"
        )
    return valor, detalhes


def variance(valores, **opcoes):
    media = math.fsum(valores) / len(valores)
    desvios = [(valor - media) ** 2 for valor in valores]
    variancia = math.fsum(desvios) / len(valores)
    return variancia, [
        f"Média: {formatar_numero(media)}",
        f"Desvios ao quadrado: {formatar_valores(desvios)}",
        f"Variância populacional: {formatar_numero(math.fsum(desvios))} / "
        f"{len(valores)} = {formatar_numero(variancia)}",
    ]


def stddev(valores, **opcoes):
    variancia, detalhes = variance(valores)
    desvio = math.sqrt(variancia)
    return desvio, detalhes + [
        f"Desvio padrão: √{formatar_numero(variancia)} ≈ "
        f"{formatar_numero(desvio)}"
    ]


def range_value(valores, **opcoes):
    menor = min(valores)
    maior = max(valores)
    amplitude = maior - menor
    return amplitude, [
        f"Maior valor: {formatar_numero(maior)}",
        f"Menor valor: {formatar_numero(menor)}",
        f"Amplitude: {formatar_numero(maior)} - {formatar_numero(menor)} = "
        f"{formatar_numero(amplitude)}",
    ]


def count_distinct(valores, **opcoes):
    distintos = sorted(set(valores))
    return len(distintos), [
        f"Valores distintos: {formatar_valores(distintos)}",
        f"Quantidade de valores distintos: {len(distintos)}",
    ]


def count_values(valores, **opcoes):
    frequencias = dict(sorted(Counter(valores).items()))
    tabela = "; ".join(
        f"{formatar_numero(valor)} → {frequencia}"
        for valor, frequencia in frequencias.items()
    )
    return frequencias, [f"Frequências: {tabela}"]


def increase(valores, **opcoes):
    exigir_minimo(valores, 2, "increase")
    total, linhas = aumento_contador(valores)
    return total, linhas + [
        f"Aumento total do contador: {formatar_numero(total)}"
    ]


def rate(valores, intervalo=1.0, **opcoes):
    exigir_minimo(valores, 2, "rate")
    total, linhas = aumento_contador(valores)
    tempo = tempo_decorrido(valores, intervalo)
    taxa = total / tempo
    return taxa, [
        f"Intervalo entre amostras: {formatar_numero(intervalo)} s",
        f"Tempo decorrido: ({len(valores)} - 1) × "
        f"{formatar_numero(intervalo)} = {formatar_numero(tempo)} s",
    ] + linhas + [
        f"Taxa média: {formatar_numero(total)} / {formatar_numero(tempo)} = "
        f"{formatar_numero(taxa)} por segundo"
    ]


def irate(valores, intervalo=1.0, **opcoes):
    exigir_minimo(valores, 2, "irate")
    anterior = valores[-2]
    atual = valores[-1]
    if atual >= anterior:
        delta = atual - anterior
        explicacao = (
            f"{formatar_numero(anterior)} → {formatar_numero(atual)}: "
            f"+{formatar_numero(delta)}"
        )
    else:
        delta = atual
        explicacao = (
            f"{formatar_numero(anterior)} → {formatar_numero(atual)}: "
            f"reset detectado, contribuição +{formatar_numero(delta)}"
        )
    taxa = delta / intervalo
    return taxa, [
        f"Intervalo entre amostras: {formatar_numero(intervalo)} s",
        explicacao,
        f"Taxa instantânea: {formatar_numero(delta)} / "
        f"{formatar_numero(intervalo)} = {formatar_numero(taxa)} por segundo",
    ]


def delta(valores, **opcoes):
    exigir_minimo(valores, 2, "delta")
    primeiro = valores[0]
    ultimo = valores[-1]
    variacao = ultimo - primeiro
    return variacao, [
        f"Primeira amostra: {formatar_numero(primeiro)}",
        f"Última amostra: {formatar_numero(ultimo)}",
        f"Variação líquida: {formatar_numero(ultimo)} - "
        f"{formatar_numero(primeiro)} = {formatar_numero(variacao)}",
    ]


def idelta(valores, **opcoes):
    exigir_minimo(valores, 2, "idelta")
    anterior = valores[-2]
    atual = valores[-1]
    variacao = atual - anterior
    return variacao, [
        f"Penúltima amostra: {formatar_numero(anterior)}",
        f"Última amostra: {formatar_numero(atual)}",
        f"Variação instantânea: {formatar_numero(atual)} - "
        f"{formatar_numero(anterior)} = {formatar_numero(variacao)}",
    ]


def deriv(valores, intervalo=1.0, **opcoes):
    exigir_minimo(valores, 2, "deriv")
    inclinacao, intercepto, tempos, media_tempo, media_valor = regressao(
        valores, intervalo
    )
    return inclinacao, [
        f"Tempos: {formatar_valores(tempos)} s",
        f"Valores: {formatar_valores(valores)}",
        f"Média dos tempos: {formatar_numero(media_tempo)} s",
        f"Média dos valores: {formatar_numero(media_valor)}",
        f"Reta ajustada: valor = {formatar_numero(intercepto)} + "
        f"{formatar_numero(inclinacao)} × tempo",
        f"Inclinação: {formatar_numero(inclinacao)} por segundo",
    ]


def avg_over_time(valores, **opcoes):
    valor, detalhes = avg(valores)
    return valor, [f"Janela analisada: {len(valores)} amostra(s)."] + detalhes


def min_over_time(valores, **opcoes):
    valor, detalhes = min_value(valores)
    return valor, [f"Janela analisada: {len(valores)} amostra(s)."] + detalhes


def max_over_time(valores, **opcoes):
    valor, detalhes = max_value(valores)
    return valor, [f"Janela analisada: {len(valores)} amostra(s)."] + detalhes


def sum_over_time(valores, **opcoes):
    valor, detalhes = sum_values(valores)
    return valor, [f"Janela analisada: {len(valores)} amostra(s)."] + detalhes


def count_over_time(valores, **opcoes):
    valor, detalhes = count(valores)
    return valor, [f"Janela analisada: {len(valores)} amostra(s)."] + detalhes


def quantile_over_time(valores, p=95.0, **opcoes):
    valor, detalhes = percentile(valores, p=p)
    return valor, [f"Janela analisada: {len(valores)} amostra(s)."] + detalhes


def stddev_over_time(valores, **opcoes):
    valor, detalhes = stddev(valores)
    return valor, [f"Janela analisada: {len(valores)} amostra(s)."] + detalhes


def predict_linear(valores, intervalo=1.0, horizonte=60.0, **opcoes):
    exigir_minimo(valores, 2, "predict_linear")
    inclinacao, intercepto, tempos, media_tempo, media_valor = regressao(
        valores, intervalo
    )
    ultimo_tempo = tempos[-1]
    tempo_futuro = ultimo_tempo + horizonte
    previsao = intercepto + inclinacao * tempo_futuro
    return previsao, [
        f"Tempos: {formatar_valores(tempos)} s",
        f"Valores: {formatar_valores(valores)}",
        f"Reta ajustada: valor = {formatar_numero(intercepto)} + "
        f"{formatar_numero(inclinacao)} × tempo",
        f"Horizonte: {formatar_numero(horizonte)} s após a última amostra",
        f"Tempo previsto: {formatar_numero(tempo_futuro)} s",
        f"Previsão: {formatar_numero(intercepto)} + "
        f"{formatar_numero(inclinacao)} × {formatar_numero(tempo_futuro)} = "
        f"{formatar_numero(previsao)}",
    ]


def changes(valores, **opcoes):
    exigir_minimo(valores, 2, "changes")
    total = 0
    linhas = []
    for indice in range(1, len(valores)):
        anterior = valores[indice - 1]
        atual = valores[indice]
        if atual != anterior:
            total += 1
            linhas.append(
                f"{formatar_numero(anterior)} → {formatar_numero(atual)}: mudou"
            )
        else:
            linhas.append(
                f"{formatar_numero(anterior)} → {formatar_numero(atual)}: "
                "manteve"
            )
    return total, linhas + [f"Total de mudanças: {total}"]


def resets(valores, **opcoes):
    exigir_minimo(valores, 2, "resets")
    total = 0
    linhas = []
    for indice in range(1, len(valores)):
        anterior = valores[indice - 1]
        atual = valores[indice]
        if atual < anterior:
            total += 1
            linhas.append(
                f"{formatar_numero(anterior)} → {formatar_numero(atual)}: "
                "reset"
            )
        else:
            linhas.append(
                f"{formatar_numero(anterior)} → {formatar_numero(atual)}: "
                "sem reset"
            )
    return total, linhas + [f"Total de resets: {total}"]


def topk(valores, k=3, **opcoes):
    if k < 1:
        raise ValueError("k precisa ser maior que zero")
    if k > len(valores):
        raise ValueError(
            f"k ({k}) não pode ser maior que a quantidade de valores "
            f"({len(valores)})"
        )
    ordenados = sorted(valores, reverse=True)
    selecionados = ordenados[:k]
    return selecionados, [
        f"Valores em ordem decrescente: {formatar_valores(ordenados)}",
        f"k = {k}",
        f"Selecionados: {formatar_valores(selecionados)}",
    ]


def bottomk(valores, k=3, **opcoes):
    if k < 1:
        raise ValueError("k precisa ser maior que zero")
    if k > len(valores):
        raise ValueError(
            f"k ({k}) não pode ser maior que a quantidade de valores "
            f"({len(valores)})"
        )
    ordenados = sorted(valores)
    selecionados = ordenados[:k]
    return selecionados, [
        f"Valores em ordem crescente: {formatar_valores(ordenados)}",
        f"k = {k}",
        f"Selecionados: {formatar_valores(selecionados)}",
    ]


def absent(valores, **opcoes):
    if valores:
        return 0, [
            f"Foram informados {len(valores)} valor(es).",
            "A métrica está presente; a ausência não seria detectada.",
        ]
    return 1, [
        "Nenhum valor foi informado.",
        "A métrica está ausente; o alerta de ausência seria disparado.",
    ]


FUNCOES = {
    "count": count,
    "sum": sum_values,
    "avg": avg,
    "min": min_value,
    "max": max_value,
    "median": median,
    "mode": mode,
    "percentile": percentile,
    "stddev": stddev,
    "variance": variance,
    "range": range_value,
    "count_distinct": count_distinct,
    "count_values": count_values,
    "rate": rate,
    "irate": irate,
    "increase": increase,
    "delta": delta,
    "idelta": idelta,
    "deriv": deriv,
    "avg_over_time": avg_over_time,
    "min_over_time": min_over_time,
    "max_over_time": max_over_time,
    "sum_over_time": sum_over_time,
    "count_over_time": count_over_time,
    "quantile_over_time": quantile_over_time,
    "stddev_over_time": stddev_over_time,
    "predict_linear": predict_linear,
    "changes": changes,
    "resets": resets,
    "topk": topk,
    "bottomk": bottomk,
    "absent": absent,
}

ALIASES = {
    "mean": "avg",
    "quantile": "percentile",
}

FUNCOES_BASICAS = [
    "count",
    "sum",
    "avg",
    "min",
    "max",
    "median",
    "mode",
    "percentile",
    "stddev",
    "variance",
    "range",
    "count_distinct",
    "count_values",
]

FUNCOES_TEMPORAIS = [
    "rate",
    "irate",
    "increase",
    "delta",
    "idelta",
    "deriv",
    "avg_over_time",
    "min_over_time",
    "max_over_time",
    "sum_over_time",
    "count_over_time",
    "quantile_over_time",
    "stddev_over_time",
    "predict_linear",
    "changes",
    "resets",
]

FUNCOES_RANKING = ["topk", "bottomk", "absent"]

FUNCOES_MINIMO_DUAS_AMOSTRAS = {
    "rate",
    "irate",
    "increase",
    "delta",
    "idelta",
    "deriv",
    "predict_linear",
    "changes",
    "resets",
}

DESCRICOES = {
    "count": (
        "contagem",
        "quantidade de amostras na lista.",
        "Ajuda a dimensionar a janela e a cardinalidade dos dados.",
    ),
    "sum": (
        "soma",
        "somatório de todas as amostras.",
        "Útil para volumes e totais; não mostra como os valores se distribuem.",
    ),
    "avg": (
        "média aritmética",
        "soma dividida pela quantidade de amostras.",
        "É sensível a outliers; compare com a mediana e os percentis.",
    ),
    "min": (
        "mínimo",
        "menor valor da lista.",
        "Ajuda a detectar pisos e valores anômalos para baixo.",
    ),
    "max": (
        "máximo",
        "maior valor da lista.",
        "Ajuda a detectar picos, mas é muito sensível a valores extremos.",
    ),
    "median": (
        "mediana",
        "valor central da lista ordenada, equivalente ao p50.",
        "É robusta a outliers e costuma representar melhor a latência típica.",
    ),
    "mode": (
        "moda",
        "valor ou valores mais frequentes.",
        "Mostra o valor mais comum; pode haver empate entre várias modas.",
    ),
    "percentile": (
        "percentil",
        "valor abaixo do qual está uma fração das amostras.",
        "Percentis altos, como p95 e p99, revelam a cauda da distribuição.",
    ),
    "stddev": (
        "desvio padrão",
        "raiz quadrada da variância populacional.",
        "Mede dispersão; um valor alto indica amostras mais espalhadas.",
    ),
    "variance": (
        "variância",
        "média dos desvios ao quadrado em relação à média.",
        "É a base do desvio padrão e fica na unidade ao quadrado.",
    ),
    "range": (
        "amplitude",
        "diferença entre o maior e o menor valor.",
        "Mostra a extensão total, mas é muito influenciada por extremos.",
    ),
    "count_distinct": (
        "contagem de distintos",
        "quantidade de valores únicos na lista.",
        "Ajuda a medir cardinalidade e variedade dos dados.",
    ),
    "count_values": (
        "contagem por valor",
        "frequência de cada valor distinto.",
        "Mostra como as amostras se distribuem entre os valores.",
    ),
    "rate": (
        "taxa média por segundo",
        "aumento do contador dividido pelo tempo decorrido.",
        "É usada com contadores monotônicos, como requisições totais.",
    ),
    "irate": (
        "taxa instantânea por segundo",
        "variação entre as duas últimas amostras dividida pelo intervalo.",
        "Reage rapidamente a mudanças recentes, mas usa pouca história.",
    ),
    "increase": (
        "aumento do contador",
        "crescimento total do contador na janela, corrigindo resets.",
        "Indica quanto um contador cresceu no período analisado.",
    ),
    "delta": (
        "diferença em medidor",
        "variação entre a última e a primeira amostra.",
        "Para gauges, mostra a mudança líquida ao longo da janela.",
    ),
    "idelta": (
        "diferença instantânea em medidor",
        "variação entre as duas últimas amostras.",
        "Mostra o movimento mais recente de um gauge.",
    ),
    "deriv": (
        "derivada/tendência",
        "inclinação da reta de regressão linear, por segundo.",
        "Indica a direção e a velocidade da tendência dos dados.",
    ),
    "avg_over_time": (
        "média na janela",
        "média das amostras da janela.",
        "Suaviza variações e resume o comportamento do período.",
    ),
    "min_over_time": (
        "mínimo na janela",
        "menor amostra da janela.",
        "Detecta o piso dentro do período analisado.",
    ),
    "max_over_time": (
        "máximo na janela",
        "maior amostra da janela.",
        "Detecta o pico dentro do período analisado.",
    ),
    "sum_over_time": (
        "soma na janela",
        "soma das amostras da janela.",
        "Útil para totais acumulados dentro de um período.",
    ),
    "count_over_time": (
        "contagem na janela",
        "quantidade de amostras na janela.",
        "Indica a densidade de amostras disponíveis no período.",
    ),
    "quantile_over_time": (
        "percentil na janela",
        "percentil das amostras da janela.",
        "Revela a cauda da distribuição dentro do período.",
    ),
    "stddev_over_time": (
        "desvio padrão na janela",
        "desvio padrão populacional das amostras da janela.",
        "Mostra a dispersão dos valores dentro do período.",
    ),
    "predict_linear": (
        "previsão linear",
        "projeção da reta de regressão para um horizonte futuro.",
        "Ajuda a prever quando um recurso pode atingir um limite.",
    ),
    "changes": (
        "mudanças",
        "quantidade de vezes em que o valor mudou entre amostras consecutivas.",
        "Detecta alternâncias em gauges e indica instabilidade.",
    ),
    "resets": (
        "resets",
        "quantidade de quedas entre amostras consecutivas.",
        "Detecta reinícios em contadores monotônicos.",
    ),
    "topk": (
        "maiores k valores",
        "os k maiores valores da lista.",
        "Ajuda a montar rankings, como as séries de maior consumo.",
    ),
    "bottomk": (
        "menores k valores",
        "os k menores valores da lista.",
        "Ajuda a montar rankings, como as séries de menor taxa.",
    ),
    "absent": (
        "ausência de dados",
        "1 quando a lista está vazia e 0 quando há dados.",
        "É inspirada em alertas de ausência de métrica no Prometheus.",
    ),
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Exercita funções de agregação de métricas, mostrando o "
            "conceito, o cálculo passo a passo e o resultado."
        ),
        epilog=(
            "Exemplos: ./script-agregacao.py -f avg 10 20 30 40 | "
            "./script-agregacao.py -f p95 10,20,30,40,50 | "
            "./script-agregacao.py --list"
        ),
    )
    parser.add_argument(
        "-f",
        "--func",
        help="Função de agregação a executar (use --list para ver as opções).",
    )
    parser.add_argument(
        "--p",
        type=float,
        default=None,
        metavar="PERCENTIL",
        help=(
            "Percentil entre 0 e 100 para percentile, quantile e "
            "quantile_over_time (padrão: 95)."
        ),
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SEGUNDOS",
        help="Intervalo entre amostras, em segundos (padrão: 1).",
    )
    parser.add_argument(
        "--horizon",
        type=float,
        default=60.0,
        metavar="SEGUNDOS",
        help="Horizonte de previsão para predict_linear (padrão: 60).",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=3,
        metavar="N",
        help="Quantidade de itens para topk/bottomk (padrão: 3).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista as funções disponíveis e exemplos de uso.",
    )
    parser.add_argument(
        "valores",
        nargs="*",
        help="Lista de valores separados por espaço ou vírgula.",
    )
    return parser.parse_args()


def resolver_funcao(escolha, p_informado):
    original = escolha.strip().lower()
    if not original:
        raise ValueError("informe o nome da função")

    if original.startswith("p") and original[1:].replace(".", "", 1).isdigit():
        if p_informado is not None:
            raise ValueError(
                "informe o percentil de uma única forma: "
                "-f p95 ou -f percentile --p 95"
            )
        percentil = float(original[1:])
        exibicao = f"{original} (percentil {formatar_numero(percentil)})"
        return "percentile", percentil, exibicao

    nome = ALIASES.get(original, original)
    if nome not in FUNCOES:
        raise ValueError(
            f"função desconhecida: {escolha}. Use --list para ver as opções"
        )
    percentil = 95.0 if p_informado is None else p_informado
    exibicao = nome if original == nome else f"{original} (alias de {nome})"
    return nome, percentil, exibicao


def validar_opcoes(args, percentil):
    if not math.isfinite(args.interval) or args.interval <= 0:
        raise ValueError("--interval precisa ser um número maior que zero")
    if not math.isfinite(args.horizon) or args.horizon < 0:
        raise ValueError("--horizon precisa ser um número maior ou igual a zero")
    if args.k < 1:
        raise ValueError("--k precisa ser um inteiro maior que zero")
    if percentil is not None and not (0 <= percentil <= 100):
        raise ValueError("o percentil precisa estar entre 0 e 100")


def obter_valores(argumentos, permitir_vazio):
    tokens = []
    for argumento in argumentos:
        tokens.extend(argumento.replace(",", " ").split())

    if not tokens:
        if permitir_vazio:
            return []
        if not sys.stdin.isatty():
            raise ValueError(
                "informe a lista de valores como argumentos "
                "(ex.: -f avg 10 20 30)"
            )
        try:
            entrada = input(
                ">> Informe os valores separados por espaço ou vírgula: "
            )
        except EOFError as erro:
            raise ValueError("nenhum valor foi informado") from erro
        tokens = entrada.replace(",", " ").split()

    if not tokens:
        raise ValueError("informe pelo menos um valor")

    valores = []
    for token in tokens:
        try:
            valor = float(token)
        except ValueError as erro:
            raise ValueError(
                f"valor inválido: {token!r}. Informe apenas números."
            ) from erro
        if not math.isfinite(valor):
            raise ValueError(
                "informe apenas números finitos (sem NaN ou infinito)"
            )
        valores.append(valor)
    return valores


def exibir_lista():
    print(">> Funções de agregação disponíveis:")
    for titulo, grupo in (
        ("Básicas", FUNCOES_BASICAS),
        ("Temporais", FUNCOES_TEMPORAIS),
        ("Ranking e detecção", FUNCOES_RANKING),
    ):
        print()
        print(f"{titulo}:")
        for nome in grupo:
            funcao_titulo, conceito, _ = DESCRICOES[nome]
            print(f"  {nome:<20} {funcao_titulo} — {conceito}")
    print()
    print("Aliases:")
    print("  mean              alias de avg")
    print("  quantile          alias de percentile")
    print("  pXX               atalho para percentil XX (ex.: p90, p95, p99)")
    print()
    print("Exemplos:")
    print("  ./script-agregacao.py -f avg 10 20 30 40")
    print("  ./script-agregacao.py -f p95 10,20,30,40,50")
    print("  ./script-agregacao.py -f rate --interval 5 100 120 150")
    print("  ./script-agregacao.py -f predict_linear --interval 60 --horizon 300 10 20 30")
    print("  ./script-agregacao.py -f absent")


def exibir(exibicao, nome, valores, resultado, detalhes):
    titulo, conceito, leitura = DESCRICOES[nome]
    print(f">> Função: {exibicao} — {titulo}")
    if valores:
        print(f">> Valores: {formatar_valores(valores)}")
    else:
        print(">> Valores: (nenhum)")
    print(f">> Conceito: {conceito}")
    print()
    for linha in detalhes:
        print(f"   {linha}")
    print()
    print(f">> Resultado: {formatar_resultado(resultado)}")
    print(f">> Leitura: {leitura}")


def main():
    args = parse_args()

    if args.list:
        exibir_lista()
        return

    try:
        if not args.func:
            raise ValueError(
                "informe a função com -f/--func (use --list para ver as opções)"
            )
        nome, percentil, exibicao = resolver_funcao(args.func, args.p)
        validar_opcoes(args, percentil)
        valores = obter_valores(args.valores, permitir_vazio=(nome == "absent"))
        if nome != "absent" and not valores:
            raise ValueError("informe pelo menos um valor")
        if nome in FUNCOES_MINIMO_DUAS_AMOSTRAS and len(valores) < 2:
            raise ValueError(f"a função {nome} exige pelo menos 2 amostras")

        resultado, detalhes = FUNCOES[nome](
            valores,
            p=percentil,
            intervalo=args.interval,
            horizonte=args.horizon,
            k=args.k,
        )
    except ValueError as erro:
        print(f">> Erro: {erro}", file=sys.stderr)
        sys.exit(1)

    exibir(exibicao, nome, valores, resultado, detalhes)


if __name__ == "__main__":
    main()
