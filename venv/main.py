import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Função auxiliar para limpar o texto do preço e converter para número (float)
def limpar_preco(texto_preco):
    try:
        texto_limpo = texto_preco.replace('R$', '').replace('\n', '').strip()
        texto_limpo = texto_limpo.replace('.', '') # Remove os pontos de milhar
        texto_limpo = texto_limpo.replace(',', '.') # Troca vírgula por ponto
        return float(texto_limpo)
    except ValueError:
        return float('inf') # Se não for possível converter (ex: "Esgotado"), retorna infinito

urlMarketPlace = {
    # "https://www.kabum.com.br": [
    #     "//input[@id='inputBusca']", # XPath relativo muito mais seguro
    #     "KaBuM", 
    #     "(//span[contains(@class, 'text-base font-semibold text-gray-800')])[{a}]",
    #     "(//h1[contains(@class, 'text-sm font-semibold text-gray-800 desktop:text-base desktopLarge:text-xl')])",
    #     "(//span[contains(@class, 'text-2xl leading-tight')])"
    # ],
    # "https://www.amazon.com.br": [
    #     "//input[@id='twotabsearchtextbox']", 
    #     "Amazon", 
    #     "(//span[contains(@class, 'a-price-whole')])[{a}]",
    #     "(//span[contains(@id, 'productTitle')])",
    #     "(//span[contains(@class, 'a-price-whole')])"
    # ],
    "https://www.efacil.com.br": [
        "(//input[@class='MuiInputBase-input MuiInputBase-inputAdornedEnd'])", 
        "eFácil", 
        "(//span[contains(@class, 'MuiTypography-root sc-5ee6e43b-0 dfUWFb sc-866b0dcf-1 hNQjWV')])[{a}]",
        "(//h1[contains(@class, 'MuiTypography-root sc-5ee6e43b-0 bGVoZF sc-58f9322b-0 heTwnA MuiTypography-h1')])",
        "(//span[contains(@class, 'MuiTypography-root sc-5ee6e43b-0 jMzKCH sc-caaf7b2-5 eQtJgk')])"
    ]
}

# Separação correta de variáveis
tem_url = input("Voce possui a URL do item? (S/N): ").strip().upper()
if tem_url == "S":
    linkProd = input("Digite a URL do item: ")
    loja = input("Digite o nome da loja: ")
    termo_busca = ""
else:
    termo_busca = input("Digite o nome do item que deseja buscar: ")

# Inicializando o Driver
driver = webdriver.Edge()
wait = WebDriverWait(driver, 20) # Vai esperar ATÉ 20 segundos pelos elementos

def buscar_marketplaceListado(driver, url, valor, termo):
    xpath_busca = valor[0]
    nome_site = valor[1]
    xpath_preco = valor[2]
    xpath_titulo = valor[3]

    print(f"\n--- Iniciando busca em {nome_site} ---")
    driver.get(url)

    try:
        busca = wait.until(EC.presence_of_element_located((By.XPATH, xpath_busca)))
        if "Não é possível" in driver.title :
            driver.refresh()

        busca.clear()
        busca.send_keys(termo)
        busca.send_keys(Keys.RETURN)
        
        # Espera a página de resultados carregar (esperando pelo primeiro preço aparecer)
        
    except Exception as e:
        print(f"Erro ao buscar no site {nome_site} ou campo de busca não encontrado.")
        return {"marketplace": nome_site, "preco": "Erro na busca"}

    menor_preco_valor = float('inf')

    # Busca os 10 primeiros itens
    for i in range(1, 11, 1):
        try:
            # Pega o elemento. Modifiquei a string do XPath para envolver com () para usar indexação relativa
            while True:
                elemento_preco = driver.find_element(By.XPATH, xpath_preco.format(a=i))
                preco_texto = elemento_preco.text
                if(preco_texto):
                    break
            
            
            if preco_texto:
                preco_float = limpar_preco(preco_texto)
                
                # Atualiza se encontrou um preço menor válido
                if preco_float < menor_preco_valor:
                    menor_preco_valor = preco_float

        except Exception:
            # Se não encontrar o item (ex: só tinham 5 produtos na tela), interrompe o laço
            break

    if menor_preco_valor != float('inf'):
        print(f"Menor preço encontrado em {nome_site} nos 10 primeiros itens: R$ {menor_preco_valor}")
        tabelaProduto = info_melhor_preco(driver, menor_preco_valor, xpath_preco, xpath_titulo)
        return {"nome_produto" : tabelaProduto["nome do produto"], "url" : tabelaProduto["link"],"marketplace": nome_site, "preco": menor_preco_valor}
    else:
        return {"marketplace": nome_site, "preco": "Nenhum preço válido encontrado"}

def info_melhor_preco(driver : webdriver, valor : float, xpathPrecoGrid:str, xpathTitulo:str):
    for i in range(1, 11, 1):
        wait.until(EC.presence_of_element_located((By.XPATH, xpathPrecoGrid.format(a=i))))
        try:
            # Pega o elemento. Modifiquei a string do XPath para envolver com () para usar indexação relativa
            acha_preco = driver.find_element(By.XPATH, xpathPrecoGrid.format(a=i))
            preco_texto = acha_preco.text
            
            if preco_texto:
                preco_float = limpar_preco(preco_texto)
                
            if(preco_float == valor):
                acha_preco.click()
                break
        except Exception:
            break
    
    titulo = driver.find_element(By.XPATH, xpathTitulo).text

    return {
        "nome do produto" : str(titulo),
        "link" : str(driver.current_url),
        "preço" : str(preco_float)
    }
    #clica em cima da div do produto
    #retorna o nome, o link, e o preco

def tabela_preco(dados : dict):
    print("*"*45)
    print(f"{"LOJA:":<15} {"NOME:":^15} {"PRECO:":>15}")
    print("*"*45)
    if "url" in dados.keys():
        print(f"{(dados["marketplace"]):<15} {(dados["url"]):^15} {(dados["preco"]):>15}")
    else:
        print("Não foi possível identificar a pagina do seu produto.")
# Execução do Código Principal
if termo_busca:
    for link, dados in urlMarketPlace.items():
        resultado = buscar_marketplaceListado(driver, link, dados, termo_busca)
        tabela_preco(resultado)

driver.quit()