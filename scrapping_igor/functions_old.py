from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from unidecode import unidecode
import requests
import pandas as pd


def get_municipios():
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    response = requests.get(url)
    # Verificação se a API está disponível
    if response.status_code == 200:
        municipios = response.json()
        nomes_municipios = []
    # Executa uma iteração entre os municípios para retirar acentuações para buscar no Banco do Brasil    
        for municipio in municipios:
            nome_municipio = municipio['nome']
            nomes_municipios.append(unidecode(nome_municipio))

    return nomes_municipios


# Função para configurar o driver
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)


# Função para processar um lote de municípios
def process_municipios_lote(municipios_lote):
    driver = setup_driver()
    try:
        for municipio in municipios_lote:
            # Abre a URL desejada
            url = "https://www42.bb.com.br/portalbb/daf/beneficiario,802,4647,4652,0,1.bbx"
            driver.get(url)

            # Aguarda até que o campo de texto esteja presente
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.ID, "formulario:txtBenef")))

            # Entra o nome do município
            input_benef = driver.find_element(By.ID, "formulario:txtBenef")
            input_benef.send_keys(municipio)

            # Clica no botão "Continuar"
            submit_button = driver.find_element(By.NAME, "formulario:j_id16")
            submit_button.click()

            # Aguarda até que o campo de data inicial esteja presente
            wait.until(EC.presence_of_element_located((By.ID, "formulario:dataInicial")))

            # Obtém a data inicial e final do mês corrente
            now = datetime.now()
            first_day_of_month = now.replace(day=1).strftime('%d/%m/%Y')
            last_day_of_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            last_day_of_month = last_day_of_month.strftime('%d/%m/%Y')

            # Insere a data inicial
            input_data_inicial = driver.find_element(By.ID, "formulario:dataInicial")
            input_data_inicial.send_keys(first_day_of_month)

            # Insere a data final
            input_data_final = driver.find_element(By.ID, "formulario:dataFinal")
            input_data_final.send_keys(last_day_of_month)

            # Confirma os dados
            submit_button_final = driver.find_element(By.NAME, "formulario:j_id20")
            submit_button_final.click()

            # Aguarda até que a tabela esteja presente
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="formulario:demonstrativoList"]')))

            # Pegue o conteúdo da página
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # Encontrar a tabela pelo ID
            table = soup.find('table', {'id': 'formulario:demonstrativoList'})
            obj_dados = {}
            lista_dados = []

            # Extrair dados da tabela
            for row in table.find_all('tr', class_=['rich-subtable-row', 'rich-subtable-row-alt']):
                cols = row.find_all('td')
                if len(cols) >= 3:
                    date = cols[0].text.strip()
                    description = cols[1].text.strip()
                    value = cols[2].text.strip()
                    linha_obj = {'data': date, 'descrição': description, 'valor': value}
                    
                    if not (
                        (linha_obj['data'] == '' and linha_obj['descrição'] == '' and linha_obj['valor'] == '') or
                        (linha_obj['data'] == 'DATA' and linha_obj['descrição'] == 'PARCELA' and linha_obj['valor'] == 'VALOR DISTRIBUIDO') or
                        (linha_obj['data'] == 'TOTAIS')
                    ):
                        lista_dados.append(linha_obj)

            obj_dados = lista_dados
            print(obj_dados)
            # df = pd.DataFrame(obj)
            # df.to_csv(f'./csv/{municipio}.csv', index=False)
    except Exception as e:
        print(f'Erro com o município {municipio}')
        # print(e)
    
    finally:
        driver.quit()