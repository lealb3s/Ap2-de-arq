"""Cobertura de arquivos originais e esquemas AP1; não exige Streamlit."""
from pathlib import Path
from types import SimpleNamespace
import pytest
from utils.importacao import ler_tabela, inspecionar_abas, ler_bruto, escolher_cabecalho, aliases_barco
from utils.mapeamento import sugestao_coluna, identificar_tipo_tabela
from utils.dados import ler, tabela_para_lista, COLUNAS_HIDRO, numero_localizado
from modules.validacao import ordenar_hidro_tabela

ROOT=Path('/mnt/data')


def arquivo(path):
    return SimpleNamespace(name=path.name,getvalue=lambda:path.read_bytes())


def test_real_multiaba_classificacao_e_dados_principais():
    p=ROOT/'hydrostatic_table (1)(1).xlsx'
    if not p.is_file():pytest.skip('Arquivo original não presente no pacote distribuído')
    f=arquivo(p)
    infos=inspecionar_abas(f)
    tipos={r['aba']:r['tipo'] for r in infos}
    assert tipos['Hydrostatic Table']=='hidro'
    assert tipos['Dados principais']=='barco'
    assert tipos['Tabela de trabalho'] is None
    assert tipos['Origem das celulas'] is None
    assert tipos['Historico'] is None
    d=ler(f,'barco',aba='Dados principais')
    assert d['nome']=='teste'
    assert float(d['B_m'])==pytest.approx(5.3)
    assert float(d['D_m'])==pytest.approx(2.7)
    assert float(d['calado_m'])==pytest.approx(1.8)
    assert 'L_m' not in d  # LPP não é necessariamente LOA


def test_real_hidro_single_multi_sheet():
    for filename,tab in [('hydrostatic_table (1)(1).xlsx','Hydrostatic Table'),
                         ('tabela hidrostática.xlsx','Planilha1')]:
        p=ROOT/filename
        if not p.is_file():continue
        f=arquivo(p)
        rows=ler(f,'hidro',aba=tab)
        mapping={c:sugestao_coluna('hidro',c,rows[0]) for c in COLUNAS_HIDRO}
        records=tabela_para_lista([{c: r.get(mapping[c]) if mapping[c] else None for c in COLUNAS_HIDRO}
                                  for r in rows],COLUNAS_HIDRO)
        for r in records:r['deslocamento_kg']*=1000.0
        records=ordenar_hidro_tabela(records)
        assert len(records)==9
        assert records[0]['deslocamento_kg']==pytest.approx(1116.125288)
        assert records[-1]['deslocamento_kg']==pytest.approx(96608.79,rel=0.00001)
        assert records[-1]['km_m']==pytest.approx(2.9055,rel=0.0001)


def test_cabecalho_deslocado_e_linhas_vazias_csv():
    sample=b'Nota;nao importar\n\ndeslocamento_kg;calado_m;km_m\n1000;1,0;2,0\n\n2000;2,0;3,0\n'
    file=SimpleNamespace(name='dados.csv',getvalue=lambda:sample)
    header,categoria=escolher_cabecalho(ler_bruto(file))
    assert categoria=='hidro'
    assert header==2
    rows=ler_tabela(file)
    data=tabela_para_lista(rows,['deslocamento_kg','calado_m','km_m'],decimal_virgula=True)
    assert len(data)==2
    assert data[0]['calado_m']==pytest.approx(1.0)
    assert data[1]['km_m']==pytest.approx(3.0)


def test_numero_br_e_erro_explicito():
    assert numero_localizado('1.234,56','m',True)==pytest.approx(1234.56)
    assert numero_localizado('1,25','m',True)==pytest.approx(1.25)
    with pytest.raises(ValueError,match='vírgula'):
        numero_localizado('1,25','m',False)


def test_carga_ficticia_so_para_validacao_do_importador():
    sample=('nome;massa [kg];X [m];Y [m];Z [m]\n'
            'caixa;100;1,2;0,5;0,8\n').encode()
    f=SimpleNamespace(name='cargas.csv',getvalue=lambda:sample)
    rows=ler(f,'cargas')
    assert identificar_tipo_tabela(rows[0])=='cargas'
    from utils.mapeamento import sugestao_coluna
    cols=['nome','massa_kg','x_m','y_m','z_m']
    map_={c:sugestao_coluna('cargas',c,rows[0]) for c in cols}
    rec=tabela_para_lista([{c:r[map_[c]] for c in cols} for r in rows],cols,decimal_virgula=True)
    assert rec[0]['x_m']==pytest.approx(1.2)


def test_ficha_grandeza_valor():
    f=SimpleNamespace(name='ficha.csv',getvalue=lambda:b'Grandeza;Valor\nnome;Navio X\nB;5.3\nD;2.7\nLPP;18\n')
    raw=ler(f,'barco')
    assert raw['B_m']=='5.3'
    assert 'L_m' not in raw


def test_unidade_literal_impede_erro_1000x():
    from utils.importacao import verificar_unidade_declarada
    assert verificar_unidade_declarada('Delta (deslocamento) [t]','t','deslocamento')
    assert verificar_unidade_declarada('km_m','m','km')
    with pytest.raises(ValueError,match='declara unidade'):
        verificar_unidade_declarada('Delta (deslocamento) [t]','kg','deslocamento')
    with pytest.raises(ValueError,match='declara unidade'):
        verificar_unidade_declarada('KM_t [m]','mm','KM transversal')
