from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Função para configurar o driver
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Executar no modo headless (sem interface gráfica)
    return webdriver.Chrome(options=chrome_options)

# Função para abrir a URL e capturar as informações do elemento
def abrir_url_e_extrair_informacoes():
    driver = setup_driver()
    try:
        # Abre a URL desejada
        url = "https://www1.siop.planejamento.gov.br/QvAJAXZfc/opendoc.htm?document=IAS%2FExecucao_Orcamentaria.qvw&host=QVS%40pqlk04&anonymous=true&sheet=SH06"
        driver.get(url)

        # Captura o conteúdo da página
        html = driver.page_source

        # Localiza todos os elementos <div> que contêm o atributo title="MT"
        elements = driver.find_elements(By.XPATH, '//div[@title="MT" and contains(@class, "Qv_multiline Qv_middle")]')

        # Lista para armazenar os dados extraídos
        lista_dados = []

        # Percorre cada elemento encontrado e extrai as informações
        for element in elements:
            parent_div = element.find_element(By.XPATH, '..')  # Navega para o elemento pai <div>
            sibling_divs = parent_div.find_elements(By.XPATH, 'following-sibling::div/div')

            # Assegure-se de que existem colunas suficientes (três ou mais)
            if len(sibling_divs) >= 3:
                date = sibling_divs[0].text.strip()
                description = sibling_divs[1].text.strip()
                value = sibling_divs[2].text.strip()

                linha_obj = {
                    'data': date,
                    'descrição': description,
                    'valor': value
                }

                # Verifica se a linha não está vazia ou não é um cabeçalho/totais   
                if not (
                    (linha_obj['data'] == '' and linha_obj['descrição'] == '' and linha_obj['valor'] == '') or
                    (linha_obj['data'] == 'DATA' and linha_obj['descrição'] == 'PARCELA' and linha_obj['valor'] == 'VALOR DISTRIBUIDO') or
                    (linha_obj['data'] == 'TOTAIS')
                ):
                    lista_dados.append(linha_obj)

        # Exibe os dados extraídos
        for dado in lista_dados:
            print(dado)

    finally:
        driver.quit()  # Fecha o navegador quando terminar

# Executa a função para abrir a URL e extrair as informações
abrir_url_e_extrair_informacoes()
