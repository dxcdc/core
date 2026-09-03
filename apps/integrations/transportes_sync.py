import csv
import io
import os
import glob
import re
import unicodedata
from decimal import Decimal
from datetime import datetime
import pandas as pd
from django.db import transaction
from django.utils import timezone
from apps.integrations.models import TransporteCorrida

COLUNAS_RESUMO = [
    'ID da Corrida', 'Plataforma', 'Data Solicitação', 'Hora Solicitação',
    'Data Chegada', 'Hora Chegada', 'Serviço', 'Programa', 'Grupo',
    'Nome', 'Sobrenome', 'Nome Completo', 'Email', 'Detalhamento da despesa',
    'Valor Total', 'Distância (km)', 'Duração (min)', 'Endereço Partida',
    'Endereço Destino', 'Cidade', 'País', 'Status'
]

VAZIOS = {'', '--', 'nan', 'none', 'nat', 'null'}


def normalizar_texto(valor):
    """Normaliza textos para comparação, ignorando maiúsculas, acentos e símbolos."""
    if valor is None:
        return ''
    texto = str(valor)

    correcoes = {
        'Ã§': 'ç', 'Ã£': 'ã', 'Ã¡': 'á', 'Ã©': 'é', 'Ãª': 'ê',
        'Ã³': 'ó', 'Ã´': 'ô', 'Ãº': 'ú', 'Ã\xad': 'í', 'Ã ': 'à',
        'Ã‡': 'Ç', 'Ãƒ': 'Ã', 'Âº': 'º', 'Âª': 'ª', '\ufeff': ''
    }
    for errado, certo in correcoes.items():
        texto = texto.replace(errado, certo)

    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower().strip()
    texto = re.sub(r'[^a-z0-9]+', ' ', texto)
    return re.sub(r'\s+', ' ', texto).strip()


def valor_vazio(valor):
    return str(valor).strip().lower() in VAZIOS


def limpar_vazios(serie, padrao=''):
    """Troca marcadores como --, nan e None por vazio ou por um padrão informado."""
    return serie.astype(str).map(lambda v: padrao if valor_vazio(v) else str(v).strip())


def encontrar_coluna(df, termos):
    """Retorna o nome real da coluna no DataFrame, usando nomes possíveis em ordem de preferência."""
    colunas_norm = [(col, normalizar_texto(col)) for col in df.columns]

    for termo in termos:
        termo_norm = normalizar_texto(termo)
        if not termo_norm:
            continue

        for col, col_norm in colunas_norm:
            if col_norm == termo_norm:
                return col

        for col, col_norm in colunas_norm:
            if termo_norm in col_norm:
                return col

    return None


def serie_coluna(df, termos, padrao=''):
    """Retorna os valores de uma coluna encontrada; se não achar, retorna série padrão."""
    coluna = encontrar_coluna(df, termos)
    if coluna is None:
        return pd.Series([padrao] * len(df), index=df.index, dtype='object')
    return df[coluna]


def coalescer_colunas(df, lista_termos, padrao=''):
    """Retorna a primeira informação não vazia entre várias colunas, linha a linha."""
    resultado = pd.Series([padrao] * len(df), index=df.index, dtype='object')

    for termos in lista_termos:
        coluna = encontrar_coluna(df, termos if isinstance(termos, list) else [termos])
        if coluna is None:
            continue
        candidatos = df[coluna].astype(str).str.strip()
        mask = resultado.astype(str).map(valor_vazio) & ~candidatos.map(valor_vazio)
        resultado.loc[mask] = candidatos.loc[mask]

    return resultado


def detectar_encoding(caminho_ou_bytes):
    if isinstance(caminho_ou_bytes, (bytes, bytearray)):
        sample = caminho_ou_bytes[:4096]
        for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                sample.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        return 'latin-1'

    for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            with open(caminho_ou_bytes, 'r', encoding=encoding) as f:
                f.read(4096)
            return encoding
        except UnicodeDecodeError:
            continue
    return 'latin-1'


def _separador_da_linha(linha):
    if linha.lower().startswith('sep='):
        return linha.strip()[-1]
    try:
        dialect = csv.Sniffer().sniff(linha, delimiters=';,\t,')
        return dialect.delimiter
    except csv.Error:
        return ';' if linha.count(';') > linha.count(',') else ','


def detectar_layout_csv(caminho_ou_buffer):
    """Detecta plataforma, layout, linha do cabeçalho e separador."""
    if isinstance(caminho_ou_buffer, (bytes, bytearray, io.BytesIO, io.StringIO)):
        if isinstance(caminho_ou_buffer, io.BytesIO):
            caminho_ou_buffer.seek(0)
            raw_bytes = caminho_ou_buffer.read(8192)
            caminho_ou_buffer.seek(0)
        elif isinstance(caminho_ou_buffer, io.StringIO):
            caminho_ou_buffer.seek(0)
            linhas = [caminho_ou_buffer.readline() for _ in range(60)]
            caminho_ou_buffer.seek(0)
            raw_bytes = None
        else:
            raw_bytes = caminho_ou_buffer[:8192]

        if raw_bytes is not None:
            encoding = detectar_encoding(raw_bytes)
            linhas = raw_bytes.decode(encoding, errors='replace').splitlines(keepends=True)[:60]
        else:
            encoding = 'utf-8'
    else:
        encoding = detectar_encoding(caminho_ou_buffer)
        with open(caminho_ou_buffer, 'r', encoding=encoding, errors='replace') as f:
            linhas = f.readlines()[:60]

    sep_declarado = None
    if linhas and linhas[0].lower().startswith('sep='):
        sep_declarado = linhas[0].strip()[-1]

    for i, linha in enumerate(linhas):
        linha_norm = normalizar_texto(linha)
        sep = sep_declarado or _separador_da_linha(linha)

        if 'id da viagem uber eats' in linha_norm or 'data da solicitacao local' in linha_norm:
            return {
                'plataforma': 'Uber', 'layout': 'Uber',
                'skiprows': i, 'sep': ';', 'encoding': encoding
            }

        # Novo layout: Importa 99.
        if (
            'id da corrida' in linha_norm
            and 'tarifa' in linha_norm
            and ('data origem' in linha_norm or 'hora origem' in linha_norm)
        ):
            return {
                'plataforma': '99', 'layout': 'Importa 99',
                'skiprows': i, 'sep': sep, 'encoding': encoding
            }

        # Modelo antigo da 99.
        if (
            ('corrida' in linha_norm and ('nome do colaborador' in linha_norm or 'nome colaborador' in linha_norm))
            or 'valor da corrida' in linha_norm
        ):
            return {
                'plataforma': '99', 'layout': '99',
                'skiprows': i, 'sep': sep, 'encoding': encoding
            }

    return {
        'plataforma': 'Uber', 'layout': 'Uber',
        'skiprows': 5, 'sep': ';', 'encoding': encoding
    }


def _parse_numero(valor):
    """Converte valor textual em float, aceitando 19.46, 19,46 e 1.234,56."""
    if pd.isna(valor):
        return None

    texto = str(valor).replace('R$', '').strip()
    if valor_vazio(texto):
        return None

    texto = re.sub(r'[^0-9,.-]', '', texto)
    if texto in ('', '-', '.', ','):
        return None

    if ',' in texto and '.' in texto:
        if texto.rfind(',') > texto.rfind('.'):
            texto = texto.replace('.', '').replace(',', '.')
        else:
            texto = texto.replace(',', '')
    elif ',' in texto:
        texto = texto.replace(',', '.')

    try:
        return float(texto)
    except ValueError:
        return None


def para_numero(serie):
    return serie.map(_parse_numero)


def formatar_numero_brasil(serie, casas=2):
    numeros = para_numero(serie)
    original = serie.astype(str).str.strip()

    def formatar(valor_num, valor_original):
        if pd.isna(valor_num):
            return '' if valor_vazio(valor_original) else valor_original
        return f'{valor_num:.{casas}f}'.replace('.', ',')

    return pd.Series(
        [formatar(num, orig) for num, orig in zip(numeros, original)],
        index=serie.index,
        dtype='object'
    )


def converter_milhas_para_km(serie, casas=2):
    numeros = para_numero(serie)
    original = serie.astype(str).str.strip()

    def formatar(valor_num, valor_original):
        if pd.isna(valor_num):
            return '' if valor_vazio(valor_original) else valor_original
        return f'{valor_num * 1.60934:.{casas}f}'.replace('.', ',')

    return pd.Series(
        [formatar(num, orig) for num, orig in zip(numeros, original)],
        index=serie.index,
        dtype='object'
    )


def formatar_hora_24(serie):
    """Converte horários para HH:MM em formato 24h, aceitando AM/PM e horários nacionais."""
    original = serie.astype(str).str.strip()

    def converter(valor):
        if valor_vazio(valor):
            return ''

        texto = str(valor).strip().upper().replace(' ', '')

        match = re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?(AM|PM)$', texto)
        if match:
            hora = int(match.group(1))
            minuto = int(match.group(2))
            segundo = int(match.group(3) or 0)
            periodo = match.group(4)
            if periodo == 'AM' and hora == 12:
                hora = 0
            elif periodo == 'PM' and hora != 12:
                hora += 12
            return f'{hora:02d}:{minuto:02d}'

        match = re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$', texto)
        if match:
            hora = int(match.group(1))
            minuto = int(match.group(2))
            segundo = int(match.group(3) or 0)
            if 0 <= hora <= 23 and 0 <= minuto <= 59 and 0 <= segundo <= 59:
                return f'{hora:02d}:{minuto:02d}'

        match = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)', str(valor), flags=re.IGNORECASE)
        if match:
            return converter(match.group(1))

        return str(valor).strip()

    return pd.Series([converter(v) for v in original], index=serie.index, dtype='object')


def formatar_data_brasil_de_americano(serie):
    """Para Uber: converte datas MM/DD/AAAA para DD/MM/AAAA."""
    original = serie.astype(str).str.strip()

    def converter(valor):
        if valor_vazio(valor):
            return ''

        texto = str(valor).strip()
        match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', texto)
        if match:
            mes, dia, ano = match.groups()
            return f'{int(dia):02d}/{int(mes):02d}/{ano}'

        match_iso = re.match(r'^(\d{4})-(\d{2})-(\d{2})', texto)
        if match_iso:
            ano, mes, dia = match_iso.groups()
            return f'{dia}/{mes}/{ano}'

        return texto

    return pd.Series([converter(v) for v in original], index=serie.index, dtype='object')


def extrair_data_hora(serie, formato_data='BR'):
    """Separa campos mistos de data e hora."""
    original = serie.astype(str).str.strip()
    datas = []
    horas = []

    for valor in original:
        if valor_vazio(valor):
            datas.append('')
            horas.append('')
            continue

        texto = str(valor).strip()
        match_data = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}-\d{2}-\d{2})', texto)
        data_encontrada = match_data.group(1) if match_data else ''

        match_hora = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)', texto, flags=re.IGNORECASE)
        hora_encontrada = match_hora.group(1) if match_hora else ''

        datas.append(data_encontrada)
        horas.append(hora_encontrada)

    serie_data = pd.Series(datas, index=serie.index, dtype='object')
    serie_hora = pd.Series(horas, index=serie.index, dtype='object')

    if formato_data == 'US':
        serie_data = formatar_data_brasil_de_americano(serie_data)
    else:
        serie_data = formatar_data_brasil_de_americano(serie_data)

    serie_hora = formatar_hora_24(serie_hora)
    return serie_data, serie_hora


def traduzir_status(serie):
    original = serie.astype(str).str.strip()

    def traduzir(valor):
        if valor_vazio(valor):
            return 'Concluída'
        norm = normalizar_texto(valor)
        if 'cancel' in norm:
            return 'Cancelada'
        if 'complet' in norm or 'conclui' in norm or 'finaliz' in norm or 'ok' in norm:
            return 'Concluída'
        return str(valor).strip()

    return pd.Series([traduzir(v) for v in original], index=serie.index, dtype='object')


def preencher_status_padrao(serie, padrao='Concluída'):
    return serie.map(lambda v: padrao if valor_vazio(v) else str(v).strip())


def separar_nome_sobrenome(serie_nome_completo):
    nomes = []
    sobrenomes = []

    for valor in serie_nome_completo:
        texto = '' if valor_vazio(valor) else str(valor).strip()
        partes = texto.split()
        if not partes:
            nomes.append('')
            sobrenomes.append('')
        elif len(partes) == 1:
            nomes.append(partes[0])
            sobrenomes.append('')
        else:
            nomes.append(partes[0])
            sobrenomes.append(' '.join(partes[1:]))

    return (
        pd.Series(nomes, index=serie_nome_completo.index, dtype='object'),
        pd.Series(sobrenomes, index=serie_nome_completo.index, dtype='object')
    )


def calcular_duracao_minutos(serie_d_ini, serie_h_ini, serie_d_fim, serie_h_fim):
    duracoes = []

    for d_ini, h_ini, d_fim, h_fim in zip(serie_d_ini, serie_h_ini, serie_d_fim, serie_h_fim):
        s_d_ini, s_h_ini = str(d_ini).strip(), str(h_ini).strip()
        s_d_fim, s_h_fim = str(d_fim).strip(), str(h_fim).strip()

        if valor_vazio(s_h_ini) or valor_vazio(s_h_fim):
            duracoes.append('')
            continue

        dt_ini = None
        dt_fim = None

        if not valor_vazio(s_d_ini) and not valor_vazio(s_d_fim):
            try:
                m_d_ini = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', s_d_ini)
                m_d_fim = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', s_d_fim)
                m_h_ini = re.match(r'^(\d{2}):(\d{2})$', s_h_ini)
                m_h_fim = re.match(r'^(\d{2}):(\d{2})$', s_h_fim)

                if m_d_ini and m_d_fim and m_h_ini and m_h_fim:
                    dia_i, mes_i, ano_i = map(int, m_d_ini.groups())
                    dia_f, mes_f, ano_f = map(int, m_d_fim.groups())
                    hora_i, min_i = map(int, m_h_ini.groups())
                    hora_f, min_f = map(int, m_h_fim.groups())

                    dt_ini = datetime(year=ano_i, month=mes_i, day=dia_i, hour=hora_i, minute=min_i)
                    dt_fim = datetime(year=ano_f, month=mes_f, day=dia_f, hour=hora_f, minute=min_f)

                    if dt_fim < dt_ini and (ano_i, mes_i, dia_i) == (ano_f, mes_f, dia_f):
                        dt_fim += pd.Timedelta(days=1)
            except Exception:
                dt_ini = None
                dt_fim = None

        if dt_ini is None or dt_fim is None:
            try:
                partes_h_ini = s_h_ini.split(':')
                partes_h_fim = s_h_fim.split(':')
                if len(partes_h_ini) == 2 and len(partes_h_fim) == 2:
                    min_ini = int(partes_h_ini[0]) * 60 + int(partes_h_ini[1])
                    min_fim = int(partes_h_fim[0]) * 60 + int(partes_h_fim[1])
                    diff = min_fim - min_ini
                    if diff < 0:
                        diff += 1440
                    duracoes.append(str(diff))
                    continue
            except Exception:
                pass

        if dt_ini is not None and dt_fim is not None:
            diff_segundos = (dt_fim - dt_ini).total_seconds()
            if diff_segundos >= 0:
                duracoes.append(str(int(round(diff_segundos / 60.0))))
            else:
                duracoes.append('')
        else:
            duracoes.append('')

    return pd.Series(duracoes, index=serie_d_ini.index, dtype='object')


def montar_resumo_uber(df):
    val_num = para_numero(serie_coluna(df, [
        'Valor total: BRL',
        'Valor da transação: BRL',
        'Valor Total',
        'Valor da Corrida',
        'Tarifa'
    ]))
    mascara_validos = ~(val_num < 0)
    df = df[mascara_validos].reset_index(drop=True)
    val_num = val_num[mascara_validos].reset_index(drop=True)

    resumo = pd.DataFrame(index=df.index)
    resumo['ID da Corrida'] = serie_coluna(df, [
        'ID da viagem Uber Eats',
        'ID da viagem',
        'ID da Corrida',
        'Código da Viagem'
    ])
    resumo['Plataforma'] = 'Uber'

    col_data_hora_solicitacao = serie_coluna(df, [
        'Data da solicitação (local)', 'Data da solicitação', 'Data da Solicitacao'
    ])
    resumo['Data Solicitação'], resumo['Hora Solicitação'] = extrair_data_hora(col_data_hora_solicitacao, formato_data='US')

    col_data_hora_chegada = serie_coluna(df, [
        'Data da chegada (local)', 'Data da chegada', 'Data da Chegada'
    ])
    resumo['Data Chegada'], resumo['Hora Chegada'] = extrair_data_hora(col_data_hora_chegada, formato_data='US')

    nome_completo = coalescer_colunas(df, [
        ['Nome do passageiro'],
        ['Nome do solicitante'],
        ['Nome do cliente'],
        ['Nome Completo']
    ])
    resumo['Nome Completo'] = limpar_vazios(nome_completo)
    resumo['Nome'], resumo['Sobrenome'] = separar_nome_sobrenome(resumo['Nome Completo'])

    resumo['Email'] = coalescer_colunas(df, [
        ['E-mail do passageiro'],
        ['E-mail do solicitante'],
        ['E-mail do cliente'],
        ['Email', 'E-mail']
    ])

    resumo['Endereço Partida'] = serie_coluna(df, ['Endereço de partida', 'Endereco de partida', 'Endereço de Origem'])
    resumo['Endereço Destino'] = serie_coluna(df, ['Destino', 'Endereço de Destino', 'Endereco de Destino'])
    resumo['Cidade'] = serie_coluna(df, ['Cidade'])
    resumo['País'] = 'Brasil'

    resumo['Duração (min)'] = calcular_duracao_minutos(
        resumo['Data Solicitação'],
        resumo['Hora Solicitação'],
        resumo['Data Chegada'],
        resumo['Hora Chegada']
    )

    coluna_distancia = encontrar_coluna(df, ['Distância (mi)', 'Distancia (mi)', 'Distância (km)', 'Distancia (km)'])
    if coluna_distancia and 'km' in coluna_distancia.lower():
        resumo['Distância (km)'] = formatar_numero_brasil(df[coluna_distancia])
    elif coluna_distancia:
        resumo['Distância (km)'] = converter_milhas_para_km(df[coluna_distancia])
    else:
        resumo['Distância (km)'] = ''

    resumo['Valor Total'] = formatar_numero_brasil(val_num)
    resumo['Serviço'] = serie_coluna(df, ['Serviço', 'Servico', 'Produto'])
    resumo['Programa'] = serie_coluna(df, ['Programa', 'Projeto'])
    resumo['Grupo'] = serie_coluna(df, ['Grupo', 'Centro de Custo'])
    resumo['Detalhamento da despesa'] = serie_coluna(df, ['Detalhamento da despesa', 'Justificativa'])

    status = traduzir_status(serie_coluna(df, ['Status']))
    resumo['Status'] = preencher_status_padrao(status, 'Concluída')

    return resumo.fillna('')


def montar_resumo_99(df, layout_nome='99'):
    val_num = para_numero(serie_coluna(df, ['Tarifa', 'Valor da Corrida', 'Valor Total']))
    mascara_validos = ~(val_num < 0)
    df = df[mascara_validos].reset_index(drop=True)
    val_num = val_num[mascara_validos].reset_index(drop=True)

    resumo = pd.DataFrame(index=df.index)
    resumo['Plataforma'] = '99'
    resumo['ID da Corrida'] = serie_coluna(df, ['ID da Corrida', 'Corrida'])

    data_origem = encontrar_coluna(df, ['Data Origem'])
    hora_origem = encontrar_coluna(df, ['Hora Origem'])
    data_final = encontrar_coluna(df, ['Data Final'])
    hora_final = encontrar_coluna(df, ['Hora Final'])

    if data_origem and hora_origem:
        resumo['Data Solicitação'] = formatar_data_brasil_de_americano(df[data_origem])
        resumo['Hora Solicitação'] = formatar_hora_24(df[hora_origem])
    else:
        col_solic = serie_coluna(df, ['Horário da Solicitação', 'Data da Solicitação', 'Data da Solicitacao'])
        resumo['Data Solicitação'], resumo['Hora Solicitação'] = extrair_data_hora(col_solic, formato_data='BR')

    if data_final and hora_final:
        resumo['Data Chegada'] = formatar_data_brasil_de_americano(df[data_final])
        resumo['Hora Chegada'] = formatar_hora_24(df[hora_final])
    else:
        col_chegada = serie_coluna(df, ['Horário da Finalização', 'Data da Finalização', 'Data da Finalizacao', 'Horário de Finalização'])
        resumo['Data Chegada'], resumo['Hora Chegada'] = extrair_data_hora(col_chegada, formato_data='BR')

    nome_completo = coalescer_colunas(df, [
        ['Nome Colaborador'],
        ['Nome do Colaborador'],
        ['Passageiro'],
        ['Nome Completo']
    ])
    resumo['Nome Completo'] = limpar_vazios(nome_completo)
    resumo['Nome'], resumo['Sobrenome'] = separar_nome_sobrenome(resumo['Nome Completo'])

    resumo['Email'] = coalescer_colunas(df, [
        ['Email Colaborador'],
        ['E-mail do colaborador'],
        ['E-mail', 'Email']
    ])

    resumo['Endereço Partida'] = coalescer_colunas(df, [
        ['Endereço de Origem Real'],
        ['Endereço de Origem Solicitado'],
        ['Endereço de Origem', 'Endereco de Origem']
    ])
    resumo['Endereço Destino'] = coalescer_colunas(df, [
        ['Endereço Final Real'],
        ['Endereço Final Solicitado'],
        ['Endereço de Destino', 'Endereco de Destino']
    ])

    resumo['Cidade'] = serie_coluna(df, ['Cidade Origem', 'Cidade de Origem', 'Cidade'])
    resumo['País'] = 'Brasil'

    resumo['Distância (km)'] = formatar_numero_brasil(serie_coluna(df, [
        'Odometro (km)', 'Odômetro (km)', 'Distancia (KM)', 'Distância (KM)', 'Distância (km)'
    ]))

    resumo['Duração (min)'] = calcular_duracao_minutos(
        resumo['Data Solicitação'],
        resumo['Hora Solicitação'],
        resumo['Data Chegada'],
        resumo['Hora Chegada']
    )

    resumo['Valor Total'] = formatar_numero_brasil(val_num)
    resumo['Serviço'] = serie_coluna(df, ['Categoria', 'Serviço', 'Servico'])
    resumo['Programa'] = coalescer_colunas(df, [['Projeto'], ['Programa']])
    resumo['Grupo'] = coalescer_colunas(df, [['Centro de Custo'], ['Grupo']])
    resumo['Detalhamento da despesa'] = serie_coluna(df, ['Justificativa', 'Detalhamento da despesa'])

    status = traduzir_status(serie_coluna(df, ['Status']))
    resumo['Status'] = preencher_status_padrao(status, 'Concluída')

    return resumo.fillna('')


def processar_dataframe_para_banco(df_resumo, arquivo_origem=""):
    """
    Persiste um DataFrame de 22 colunas atômicas no PostgreSQL com idempotência e deduplicação em memória.
    """
    if df_resumo is None or df_resumo.empty:
        return 0

    from apps.integrations.models import TransporteProgramaAlias
    try:
        alias_map = {a.nome_original.lower().strip(): a.nome_padronizado for a in TransporteProgramaAlias.objects.filter(ativo=True)}
    except Exception:
        alias_map = {}

    unique_objs = {}
    for _, row in df_resumo.iterrows():
        id_corrida = str(row.get('ID da Corrida') or '').strip()
        if not id_corrida:
            continue

        plataforma = str(row.get('Plataforma') or 'Uber').strip()
        if '99' in plataforma:
            plataforma = '99'
        else:
            plataforma = 'Uber'

        # Parse datahora de inicio
        d_solic = str(row.get('Data Solicitação') or '').strip()
        h_solic = str(row.get('Hora Solicitação') or '').strip()
        dt_solic = None
        if d_solic and h_solic:
            try:
                m_d = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', d_solic)
                m_h = re.match(r'^(\d{2}):(\d{2})$', h_solic)
                if m_d and m_h:
                    dia, mes, ano = map(int, m_d.groups())
                    hora, minu = map(int, m_h.groups())
                    dt_solic = timezone.make_aware(datetime(ano, mes, dia, hora, minu))
            except Exception:
                dt_solic = None

        # Parse datahora de conclusao
        d_cheg = str(row.get('Data Chegada') or '').strip()
        h_cheg = str(row.get('Hora Chegada') or '').strip()
        dt_cheg = None
        if d_cheg and h_cheg:
            try:
                m_d = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', d_cheg)
                m_h = re.match(r'^(\d{2}):(\d{2})$', h_cheg)
                if m_d and m_h:
                    dia, mes, ano = map(int, m_d.groups())
                    hora, minu = map(int, m_h.groups())
                    dt_cheg = timezone.make_aware(datetime(ano, mes, dia, hora, minu))
            except Exception:
                dt_cheg = None

        # Valores
        v_tot_str = str(row.get('Valor Total') or '0').replace('.', '').replace(',', '.')
        try:
            v_total = Decimal(v_tot_str)
        except Exception:
            v_total = Decimal('0.00')

        dist_str = str(row.get('Distância (km)') or '').replace('.', '').replace(',', '.')
        try:
            dist_km = Decimal(dist_str) if dist_str else None
        except Exception:
            dist_km = None

        dur_str = str(row.get('Duração (min)') or '').strip()
        try:
            dur_min = int(dur_str) if dur_str else None
        except Exception:
            dur_min = None

        raw_dict = row.to_dict()

        key = (id_corrida, plataforma)
        unique_objs[key] = TransporteCorrida(
            id_corrida=id_corrida,
            plataforma=plataforma,
            data_solicitacao=d_solic,
            hora_solicitacao=h_solic,
            data_chegada=d_cheg,
            hora_chegada=h_cheg,
            solicitado_em=dt_solic,
            concluido_em=dt_cheg,
            servico=str(row.get('Serviço') or '').strip(),
            programa=alias_map.get(str(row.get('Programa') or '').strip().lower(), str(row.get('Programa') or '').strip()),
            grupo=alias_map.get(str(row.get('Grupo') or '').strip().lower(), str(row.get('Grupo') or '').strip()),
            nome=str(row.get('Nome') or '').strip(),
            sobrenome=str(row.get('Sobrenome') or '').strip(),
            nome_completo=str(row.get('Nome Completo') or '').strip(),
            email=str(row.get('Email') or '').strip(),
            detalhamento_despesa=str(row.get('Detalhamento da despesa') or '').strip(),
            valor_total=v_total,
            distancia_km=dist_km,
            duracao_minutos=dur_min,
            endereco_partida=str(row.get('Endereço Partida') or '').strip(),
            endereco_destino=str(row.get('Endereço Destino') or '').strip(),
            cidade=str(row.get('Cidade') or '').strip(),
            pais=str(row.get('País') or 'Brasil').strip(),
            status=str(row.get('Status') or 'Concluída').strip(),
            arquivo_origem=arquivo_origem,
            dados_brutos=raw_dict,
        )

    objs = list(unique_objs.values())
    if objs:
        with transaction.atomic():
            TransporteCorrida.objects.bulk_create(
                objs,
                update_conflicts=True,
                unique_fields=['id_corrida', 'plataforma'],
                update_fields=[
                    'data_solicitacao', 'hora_solicitacao', 'data_chegada', 'hora_chegada',
                    'solicitado_em', 'concluido_em', 'servico', 'programa', 'grupo',
                    'nome', 'sobrenome', 'nome_completo', 'email', 'detalhamento_despesa',
                    'valor_total', 'distancia_km', 'duracao_minutos', 'endereco_partida',
                    'endereco_destino', 'cidade', 'pais', 'status', 'arquivo_origem',
                    'dados_brutos', 'atualizado_em'
                ]
            )
    return len(objs)


def processar_arquivo_transporte(caminho_ou_buffer, nome_arquivo=""):
    """
    Processa um único arquivo (caminho no disco ou buffer em memória) e persiste no banco.
    """
    if str(nome_arquivo).endswith(('.xlsx', '.xls')):
        df_original = pd.read_excel(caminho_ou_buffer, dtype=str).fillna('')
        df_original.columns = [str(c).replace('\ufeff', '').strip() for c in df_original.columns]
        layout = {'plataforma': 'Uber', 'layout': 'Excel'}
        norm_cols = ' '.join(normalizar_texto(c) for c in df_original.columns)
        if 'tarifa' in norm_cols or 'nome colaborador' in norm_cols:
            layout['plataforma'] = '99'
            df_resumo = montar_resumo_99(df_original)
        else:
            df_resumo = montar_resumo_uber(df_original)
    else:
        layout = detectar_layout_csv(caminho_ou_buffer)
        if isinstance(caminho_ou_buffer, (bytes, bytearray, io.BytesIO, io.StringIO)):
            if isinstance(caminho_ou_buffer, io.BytesIO):
                caminho_ou_buffer.seek(0)
            df_original = pd.read_csv(
                caminho_ou_buffer,
                skiprows=layout['skiprows'],
                sep=layout['sep'],
                encoding=layout['encoding'],
                dtype=str,
                keep_default_na=False,
                engine='python'
            )
        else:
            df_original = pd.read_csv(
                caminho_ou_buffer,
                skiprows=layout['skiprows'],
                sep=layout['sep'],
                encoding=layout['encoding'],
                dtype=str,
                keep_default_na=False,
                engine='python'
            )
        df_original.columns = [str(c).replace('\ufeff', '').strip() for c in df_original.columns]

        if layout['plataforma'] == '99':
            df_resumo = montar_resumo_99(df_original, layout['layout'])
        else:
            df_resumo = montar_resumo_uber(df_original)

    total_salvo = processar_dataframe_para_banco(df_resumo, arquivo_origem=nome_arquivo)

    val_total = 0.0
    for v in df_resumo['Valor Total']:
        num = _parse_numero(v)
        if num:
            val_total += num

    return {
        'arquivo': nome_arquivo,
        'plataforma': layout.get('plataforma', 'Desconhecida'),
        'layout': layout.get('layout', 'Padrão'),
        'total_linhas': len(df_resumo),
        'total_salvo': total_salvo,
        'valor_total_brl': round(val_total, 2)
    }


def gerar_planilha_consolidada_excel(queryset=None):
    """
    Gera dinamicamente o arquivo Excel (.xlsx) com a formatação oficial.
    """
    if queryset is None:
        queryset = TransporteCorrida.objects.all().order_by('-solicitado_em', '-id')

    linhas = []
    for c in queryset:
        linhas.append({
            'ID da Corrida': c.id_corrida,
            'Plataforma': c.plataforma,
            'Data Solicitação': c.data_solicitacao,
            'Hora Solicitação': c.hora_solicitacao,
            'Data Chegada': c.data_chegada,
            'Hora Chegada': c.hora_chegada,
            'Serviço': c.servico,
            'Programa': c.programa,
            'Grupo': c.grupo,
            'Nome': c.nome,
            'Sobrenome': c.sobrenome,
            'Nome Completo': c.nome_completo,
            'Email': c.email,
            'Detalhamento da despesa': c.detalhamento_despesa,
            'Valor Total': f"{c.valor_total:.2f}".replace('.', ','),
            'Distância (km)': f"{c.distancia_km:.2f}".replace('.', ',') if c.distancia_km is not None else '',
            'Duração (min)': str(c.duracao_minutos) if c.duracao_minutos is not None else '',
            'Endereço Partida': c.endereco_partida,
            'Endereço Destino': c.endereco_destino,
            'Cidade': c.cidade,
            'País': c.pais,
            'Status': c.status,
        })

    df_resumo = pd.DataFrame(linhas, columns=COLUNAS_RESUMO) if linhas else pd.DataFrame(columns=COLUNAS_RESUMO)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_resumo.to_excel(writer, sheet_name='Resumo', index=False)
        workbook = writer.book
        formato_cabecalho = workbook.add_format({
            'bold': True,
            'bg_color': '#D9EAF7',
            'border': 1,
            'text_wrap': True,
            'valign': 'vcenter'
        })
        formato_texto = workbook.add_format({'text_wrap': True, 'valign': 'top'})

        ws = writer.sheets['Resumo']
        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(df_resumo), len(df_resumo.columns) - 1)

        for col_idx, coluna in enumerate(df_resumo.columns):
            largura = min(max(len(str(coluna)) + 2, 12), 42)
            if coluna in ['Endereço Partida', 'Endereço Destino', 'Detalhamento da despesa', 'Nome Completo', 'Email']:
                largura = 34
            if coluna in ['Data Solicitação', 'Data Chegada', 'Hora Solicitação', 'Hora Chegada']:
                largura = 16
            ws.write(0, col_idx, coluna, formato_cabecalho)
            ws.set_column(col_idx, col_idx, largura, formato_texto)

    output.seek(0)
    return output
