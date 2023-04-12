Alunos:
	Leonardo Gibrowski Faé (20280524-8)
	Ricardo Guimarães (20280681-6)

Repositório: https://github.com/Horus645/LabSysOpT1

# Tutorial para reprodução do trabalho

Essas instruções pressupões que o usuário já efetuou os passos descritos nos tutoriais 1.1, 1.2 e 1.3, disponibilizados pelo professor. Em particular, o usuário deverá
criar uma rota entre a máquina Host e a máquina Guest(QEMU)(testar com o Ping).

## Instalando o Interpretador do Python:

Abrindo o menuconfig, defina a seguinte configuração:
```
  -- Target Packeges
    -- Interpreter languages and scripting
      [*] python3 
```

* O python exige suporte para o WCHAR. Para disponibilizar o mesmo, voce derá mudar a biblioteca do C disponível na distribuição:
```
  -- Toolchain
    C library (uClibc-ng) -->
    .
    .
    .
    [*] Enable WCHAR support
```

* Salve as configurações e execute o comando `make` no terminal

## Disponibilizando o servidor SSH no Guest:

* Novamente, abrindo o menuconfig, habilite o `dropbear`

```
  -- Target packages
    -- Networking applications
      [*] dropbear
```

* Rode o `make`
* Suba a máquina emulada e configure uma senha com o comando `passwd`(pode ser vazia)
* Abra um novo terminal na máquina Host e tente conectar via SSH na Guest com o comando:
 ```ssh root@<IP da Guest>```
 * Para descobrir o IP da máquina Guest, execute o comando `ifconfig` dentro dela(IPv4 da interface eth0)
 
## Rodando o servidor HTTP

Primeiramente, edite a variável `HOST_NAME` dentro do arquivo web_server.py para o número de IP da máquina target.

### Importando o servidor HTTP para a máquina Guest via SSH:
 
* Execute o utilitário `scp` da máquina Host para transferir o arquivo contendo o código gerador do servidor HTTP(no caso, web_server.py):

``` scp web_server.py root@<IP Do Host>:/root/ ```

* OBS: Caso o comando falhe(é possível que aconteça por incompatibilidade de versão), adicione a flag -O para utilizar o protocolo legado.

### Executando o servidor

Entre na máquina target e execute o script:

```
python web_server.py
```

### Visualizando a página HTTP

A página estará disponível no endereço `<IP do Target>:8000`. Você pode acessá-la usando um browser qualquer.
