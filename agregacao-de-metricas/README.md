# Funções de agregação de métricas

Exercício didático sobre as principais funções usadas para agregar métricas em monitoramento: média, mediana, percentis, desvio padrão, taxas, tendências, rankings e detecção de ausência de dados.

O script [`script-agregacao.py`](./script-agregacao.py) implementa uma função Python para cada agregação e permite escolher a função pela linha de comando. Cada execução mostra o conceito, o cálculo passo a passo e a interpretação do resultado.

## Objetivo

Em monitoramento, raramente olhamos para uma única amostra isolada. O que interessa é responder perguntas como:

- Qual é o comportamento típico da latência?
- A cauda da distribuição está piorando?
- Quantas requisições por segundo o serviço recebe?
- O uso de disco está crescendo? Quando vai encher?
- Qual série consome mais recursos?
- A métrica parou de chegar?

Cada pergunta pede uma agregação diferente. Este exercício reúne as principais funções e mostra, com exemplos numéricos, o que cada uma calcula e quando faz sentido usá-la.

## Conceitos fundamentais

### Amostra, série e janela

- **Amostra:** um valor observado em um instante.
- **Série:** uma sequência de amostras ao longo do tempo, normalmente identificada por labels.
- **Janela:** o intervalo de tempo considerado em uma agregação temporal.

Neste exercício, a lista informada no terminal representa as amostras de uma série. Nas funções temporais, as amostras são tratadas como **igualmente espaçadas**, com o intervalo definido por `--interval` (padrão: 1 segundo).

### Gauge e counter

- **Gauge (medidor):** valor que sobe e desce, como uso de CPU, memória, temperatura ou filas. Para gauges, usamos funções como `avg`, `min`, `max`, `delta` e `idelta`.
- **Counter (contador):** valor que só cresce, como total de requisições ou bytes transmitidos. Reinícios fazem o contador voltar a zero. Para contadores, usamos `rate`, `irate` e `increase`, que corrigem esses resets.

### Agregação instantânea e temporal

- **Instantânea:** resume um conjunto de amostras em um único valor. Exemplos: `avg`, `median`, `sum`, `max`.
- **Temporal:** considera a ordem e o espaçamento das amostras. Exemplos: `rate`, `increase`, `deriv`, `predict_linear`, `changes`.

### Tendência central, dispersão e cauda

- **Tendência central:** média, mediana e moda. Resumem o valor "típico".
- **Dispersão:** variância, desvio padrão e amplitude. Mostram o quanto os valores variam.
- **Cauda:** percentis altos, como p90, p95 e p99. Mostram o comportamento dos piores casos.

A média é simples, mas sensível a valores extremos. A mediana é mais robusta. Os percentis são essenciais para latência, porque uma minoria de requisições lentas pode não mover a média, mas afeta muito a experiência do usuário.

### Percentis

O percentil `p` é o valor abaixo do qual está uma fração `p%` das amostras ordenadas. Neste script, o cálculo usa interpolação linear:

1. Ordene os valores.
2. Calcule a posição: `(p / 100) × (n - 1)`.
3. Identifique os valores inferior e superior ao redor da posição.
4. Interpole linearmente entre eles.

Exemplo com `p95` e `[10, 20, 30, 40, 50]`:

```text
posição = (95 / 100) × (5 - 1) = 3,8
valor = 40 + 0,8 × (50 - 40) = 48
```

A mediana é equivalente ao `p50`.

### Variância e desvio padrão

A variância populacional é a média dos desvios ao quadrado em relação à média:

```text
variância = Σ(valor - média)² / N
```

O desvio padrão é a raiz quadrada da variância e volta à unidade original dos dados. Neste exercício, usamos a versão **populacional**, dividindo por `N`.

### Cardinalidade

Cardinalidade é a quantidade de valores ou séries distintas. `count_distinct` conta valores únicos; `count_values` mostra a frequência de cada valor. Em monitoramento, cardinalidade alta pode aumentar custo de armazenamento e tempo de consulta.

## Catálogo de funções

As tabelas abaixo trazem pelo menos um exemplo numérico para cada função. Os comandos assumem que o script está no diretório atual.

### Funções básicas

| Função | O que calcula | Exemplo | Resultado | Comando |
| --- | --- | --- | --- | --- |
| `count` | Quantidade de amostras. | `[10, 20, 30, 40]` | `4` | `-f count 10 20 30 40` |
| `sum` | Soma de todas as amostras. | `[10, 20, 30, 40]` | `100` | `-f sum 10 20 30 40` |
| `avg` / `mean` | Média aritmética. | `[10, 20, 30, 40]` | `25` | `-f avg 10 20 30 40` |
| `min` | Menor valor. | `[10, 20, 30, 40]` | `10` | `-f min 10 20 30 40` |
| `max` | Maior valor. | `[10, 20, 30, 40]` | `40` | `-f max 10 20 30 40` |
| `median` | Valor central (`p50`). | `[10, 20, 30, 40]` | `25` | `-f median 10 20 30 40` |
| `mode` | Valor ou valores mais frequentes. | `[10, 20, 20, 30, 40]` | `20` | `-f mode 10 20 20 30 40` |
| `percentile` / `quantile` / `pXX` | Percentil `p`. | `p95 [10, 20, 30, 40, 50]` | `48` | `-f p95 10 20 30 40 50` |
| `stddev` | Desvio padrão populacional. | `[10, 20, 20, 30, 40]` | `10.198` | `-f stddev 10 20 20 30 40` |
| `variance` | Variância populacional. | `[10, 20, 20, 30, 40]` | `104` | `-f variance 10 20 20 30 40` |
| `range` | Amplitude (`max - min`). | `[10, 20, 30, 40]` | `30` | `-f range 10 20 30 40` |
| `count_distinct` | Quantidade de valores únicos. | `[10, 20, 20, 30, 40]` | `4` | `-f count_distinct 10 20 20 30 40` |
| `count_values` | Frequência de cada valor. | `[10, 20, 20, 30, 40]` | `10→1, 20→2, 30→1, 40→1` | `-f count_values 10 20 20 30 40` |

### Funções temporais

As funções temporais consideram a ordem das amostras. O intervalo padrão é `1` segundo e pode ser alterado com `--interval`.

| Função | O que calcula | Exemplo | Resultado | Comando |
| --- | --- | --- | --- | --- |
| `rate` | Taxa média por segundo, corrigindo resets. | `[100, 120, 150]`, intervalo `5` | `5/s` | `-f rate --interval 5 100 120 150` |
| `irate` | Taxa instantânea pelas duas últimas amostras. | `[100, 120, 150]`, intervalo `5` | `6/s` | `-f irate --interval 5 100 120 150` |
| `increase` | Crescimento total do contador, corrigindo resets. | `[100, 120, 150]` | `50` | `-f increase 100 120 150` |
| `delta` | Variação entre a última e a primeira amostra de um gauge. | `[100, 120, 150]` | `50` | `-f delta 100 120 150` |
| `idelta` | Variação entre as duas últimas amostras de um gauge. | `[100, 120, 150]` | `30` | `-f idelta 100 120 150` |
| `deriv` | Inclinação da regressão linear por segundo. | `[10, 20, 30]`, intervalo `1` | `10/s` | `-f deriv --interval 1 10 20 30` |
| `avg_over_time` | Média das amostras da janela. | `[10, 20, 30, 40]` | `25` | `-f avg_over_time 10 20 30 40` |
| `min_over_time` | Menor amostra da janela. | `[10, 20, 30, 40]` | `10` | `-f min_over_time 10 20 30 40` |
| `max_over_time` | Maior amostra da janela. | `[10, 20, 30, 40]` | `40` | `-f max_over_time 10 20 30 40` |
| `sum_over_time` | Soma das amostras da janela. | `[10, 20, 30, 40]` | `100` | `-f sum_over_time 10 20 30 40` |
| `count_over_time` | Quantidade de amostras da janela. | `[10, 20, 30, 40]` | `4` | `-f count_over_time 10 20 30 40` |
| `quantile_over_time` | Percentil das amostras da janela. | `p95 [10, 20, 30, 40, 50]` | `48` | `-f quantile_over_time --p 95 10 20 30 40 50` |
| `stddev_over_time` | Desvio padrão populacional da janela. | `[10, 20, 20, 30, 40]` | `10.198` | `-f stddev_over_time 10 20 20 30 40` |
| `predict_linear` | Projeção da regressão linear para um horizonte. | `[10, 20, 30]`, intervalo `1`, horizonte `5` | `80` | `-f predict_linear --interval 1 --horizon 5 10 20 30` |
| `changes` | Quantidade de mudanças entre amostras consecutivas. | `[1, 2, 2, 3, 3]` | `2` | `-f changes 1 2 2 3 3` |
| `resets` | Quantidade de quedas entre amostras consecutivas. | `[100, 120, 5, 15]` | `1` | `-f resets 100 120 5 15` |

### Ranking e detecção

| Função | O que calcula | Exemplo | Resultado | Comando |
| --- | --- | --- | --- | --- |
| `topk` | Os `k` maiores valores. | `[10, 50, 30]`, `k=2` | `50, 30` | `-f topk --k 2 10 50 30` |
| `bottomk` | Os `k` menores valores. | `[10, 50, 30]`, `k=2` | `10, 30` | `-f bottomk --k 2 10 50 30` |
| `absent` | `1` para lista vazia e `0` quando há dados. | `[]` | `1` | `-f absent` |

## Exemplos comentados

### Média, mediana e percentil

Com `[10, 20, 30, 40]`:

```shell
./script-agregacao.py -f avg 10 20 30 40
```

```text
>> Função: avg — média aritmética
>> Valores: 10, 20, 30, 40
>> Conceito: soma dividida pela quantidade de amostras.

   Soma: 100
   Quantidade de amostras: 4
   Média: 100 / 4 = 25

>> Resultado: 25
>> Leitura: É sensível a outliers; compare com a mediana e os percentis.
```

A média resume o valor típico, mas pode ser puxada por um único valor extremo. A mediana divide a lista ao meio e é mais robusta. O percentil vai além e mostra a cauda:

```shell
./script-agregacao.py -f p95 10 20 30 40 50
```

```text
>> Função: p95 (percentil 95) — percentil
>> Valores: 10, 20, 30, 40, 50
>> Conceito: valor abaixo do qual está uma fração das amostras.

   Valores ordenados: 10, 20, 30, 40, 50
   Posição: (95 / 100) × (5 - 1) = 3.8
   Interpolação: 40 + 0.8 × (50 - 40) = 48

>> Resultado: 48
>> Leitura: Percentis altos, como p95 e p99, revelam a cauda da distribuição.
```

### Variância e desvio padrão

Com `[10, 20, 20, 30, 40]`, a média é `24`. Os desvios ao quadrado são `196, 16, 16, 36, 256`, somando `520`. A variância populacional é `520 / 5 = 104` e o desvio padrão é `√104 ≈ 10.198`.

```shell
./script-agregacao.py -f stddev 10 20 20 30 40
```

O desvio padrão ajuda a distinguir séries com a mesma média, mas com dispersões diferentes. Duas séries podem ter média `24`, mas uma ter valores concentrados e a outra ter picos e vales.

### Rate, increase e resets

Para contadores, a variação bruta entre a primeira e a última amostra pode enganar quando há reset. O script corrige quedas assumindo que o contador recomeçou em zero:

```text
[100, 120, 5, 15]
100 → 120: +20
120 → 5: reset detectado, contribuição +5
5 → 15: +10
increase = 20 + 5 + 10 = 35
```

```shell
./script-agregacao.py -f increase 100 120 5 15
```

`rate` é esse aumento dividido pelo tempo decorrido. `irate` olha apenas as duas últimas amostras e reage mais rápido. `delta` e `idelta` são as versões para gauges, sem correção de reset.

### Tendência e previsão

`deriv` ajusta uma reta aos pontos `(tempo, valor)` e retorna a inclinação por segundo. `predict_linear` usa essa reta para projetar um valor futuro:

```shell
./script-agregacao.py -f predict_linear --interval 1 --horizon 5 10 20 30
```

Com valores que crescem `10` por segundo, a previsão `5` segundos após a última amostra é `80`. Em monitoramento, isso ajuda a responder "quando o disco vai encher?" ou "quando a fila vai estourar?". A previsão é uma extrapolação: se o comportamento mudar, ela deixa de valer.

### Ranking e ausência

`topk` e `bottomk` ordenam os valores e selecionam os `k` primeiros. Em PromQL, eles ranqueiam séries; aqui, ranqueiam os valores da lista.

```shell
./script-agregacao.py -f topk --k 2 10 50 30
```

`absent` é inspirada na função homônima do Prometheus: retorna `1` quando não há dados. Isso permite criar alertas para métricas que simplesmente pararam de chegar.

```shell
./script-agregacao.py -f absent
```

## Como usar

O script está em [`script-agregacao.py`](./script-agregacao.py) e requer Python 3, sem dependências externas.

```shell
# concede permissão de execução (se necessário)
chmod u+x ./script-agregacao.py

# executa uma agregação
./script-agregacao.py -f avg 10 20 30 40
```

Para ver todas as funções disponíveis:

```shell
./script-agregacao.py --list
```

### Parâmetros

| Parâmetro | Descrição |
| --- | --- |
| `-f`, `--func` | Função a executar. Obrigatória, exceto com `--list`. |
| valores posicionais | Lista de amostras separadas por espaço ou vírgula. |
| `--p PERCENTIL` | Percentil entre `0` e `100` para `percentile`, `quantile` e `quantile_over_time`. Padrão: `95`. |
| `--interval SEGUNDOS` | Intervalo entre amostras. Padrão: `1`. |
| `--horizon SEGUNDOS` | Horizonte de previsão para `predict_linear`. Padrão: `60`. |
| `--k N` | Quantidade de itens para `topk` e `bottomk`. Padrão: `3`. |
| `--list` | Lista funções, aliases e exemplos. |

### Formatos de entrada

```shell
# valores separados por espaço
./script-agregacao.py -f avg 10 20 30 40

# valores separados por vírgula
./script-agregacao.py -f avg 10,20,30,40

# percentil como atalho
./script-agregacao.py -f p99 10 20 30 40 50

# percentil com --p
./script-agregacao.py -f percentile --p 99 10 20 30 40 50

# valores negativos exigem -- antes da lista
./script-agregacao.py -f avg -- -10 0 10
```

Use ponto como separador decimal. A vírgula é usada para separar valores. Se nenhum valor for informado e o terminal for interativo, o script solicita a lista.

### Validações

O script rejeita, com código de saída `1`:

- Função desconhecida.
- Valores não numéricos, `NaN` ou infinito.
- Percentil fora do intervalo `0` a `100`.
- `--interval` menor ou igual a zero.
- `--horizon` negativo.
- `--k` menor que `1` ou maior que a quantidade de valores em `topk`/`bottomk`.
- Lista vazia para funções que exigem dados.
- Menos de duas amostras para funções temporais que precisam de variação.
- Uso simultâneo de `-f p95` e `--p`.

## Armadilhas comuns em monitoramento

- **Média não substitui percentil.** Uma média baixa pode esconder uma cauda lenta. Para latência, observe p95 e p99.
- **Não tire a média de percentis.** A média de vários p95 não é o p95 do conjunto. Agregue os dados brutos ou use histogramas.
- **p95 não é o máximo.** Cerca de 5% das amostras podem estar acima dele.
- **Outliers distorcem média, desvio padrão e amplitude.** Compare com mediana e percentis.
- **Counter não é gauge.** Use `rate`, `irate` e `increase` para contadores; `delta` e `idelta` para gauges.
- **Resets precisam de tratamento.** Um contador que reinicia pode parecer uma queda gigante se a variação for calculada ingenuamente.
- **A janela muda a resposta.** Janelas curtas reagem rápido e são ruidosas; janelas longas suavizam e podem esconder picos.
- **Cardinalidade tem custo.** Muitos valores distintos ou muitas séries aumentam armazenamento e tempo de consulta.
- **Previsão não é certeza.** `deriv` e `predict_linear` extrapolam o passado; mudanças de comportamento invalidam a projeção.

## Ferramentas de IA utilizadas

Este trabalho — o plano, o código do script e esta documentação — foi elaborado com o auxílio do **OpenCode**, utilizando o modelo **`opencode/big-pickle`**, além de revisão humana. As decisões de projeto foram discutidas e aprovadas previamente, e o resultado foi verificado por execução do script contra casos conhecidos, incluindo média, mediana, percentil, desvio padrão, taxa, aumento com reset, previsão e ausência de dados.

## Referências

- [Prometheus — Query functions](https://prometheus.io/docs/prometheus/latest/querying/functions/)
- [Prometheus — Histograms and summaries](https://prometheus.io/docs/practices/histograms/)
