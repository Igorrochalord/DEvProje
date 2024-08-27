from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from unidecode import unidecode
import requests
import pandas as pd

# Função para obter os nomes dos municípios
def get_municipios():
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    response = requests.get(url)
    if response.status_code == 200:
        municipios = response.json()
        nomes_municipios = [unidecode(municipio['nome']) for municipio in municipios]
        return nomes_municipios
    else:
        print("Erro ao acessar a API dos municípios.")
        return []

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
            url = "https://www42.bb.com.br/portalbb/daf/beneficiario,802,4647,4652,0,1.bbx"
            driver.get(url)

            # Aguarda até que o campo de texto esteja presente
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.ID, "formulario:txtBenef")))

            # Entra o nome do município
            input_benef = driver.find_element(By.ID, "formulario:txtBenef")
            input_benef.clear()  # Limpa o campo antes de inserir o novo valor
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

            # Insere a data inicial e final
            input_data_inicial = driver.find_element(By.ID, "formulario:dataInicial")
            input_data_inicial.send_keys(first_day_of_month)
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
            lista_dados = []

            # Extrair dados da tabela
            if table:
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

            # Salva os dados em um DataFrame e em um arquivo CSV
            df = pd.DataFrame(lista_dados)
            df.to_csv(f'./csv/{municipio}.csv', index=False)
            print(f'Dados para o município {municipio} salvos com sucesso.')

    except Exception as e:
        print(f'Erro com o município {municipio}: {e}')
    
    finally:
        driver.quit()

# Obtém a lista de municípios e processa em lotes
municipios = get_municipios()
if municipios:
    process_municipios_lote(municipios)
