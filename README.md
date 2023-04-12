Alunos:
  * Leonardo Gibrowski Faé (20280524-8)
  * Ricardo Guimarães (20280681-6)

Repositório: https://github.com/Horus645/LabSysOpT1

# Tutorial para reprodução do trabalho

Essas instruções pressupõem que o usuário já efetuou os passos descritos nos tutoriais 1.1, 1.2 e 1.3, disponibilizados pelo professor. Em particular, o usuário deverá
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
 * Para sair da sessão SSH, utilize Ctrl+d.
 
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

### Visualizando a página HTML

A página estará disponível no endereço `<IP do Target>:8000`. Você pode acessá-la usando um browser qualquer.
`screenshot.png` tem um exemplo de como a página será apresentada.

### Como o servidor coleta as informações da página HTML

Tirando a data e hora, todas as informações da página são geradas lendo as informações do pseudo sistema de arquivos `/proc`.
Data e hora são adquiridas com o comando `date`:

```python
def date_time():
	return os.popen("date").read()
```

Uptime foi calculado a partir de `/proc/uptime`:

```python
def uptime():
    s = read_file("/proc/uptime")
    total_seconds = float(s.split(' ')[0])
    return time_from_seconds(total_seconds)
```

As informações de cpu foram retiradas de `/proc/cpuinfo`:

```python
def procinfo():
    lines = read_file("/proc/cpuinfo").split('\n')
    ret = "<br>"
    for line in lines:
        words = line.split(':')
        key = words[0].strip()
        value = words[1].strip()
        if key == "vendor_id" or  \
           key == "cpu family" or \
           key == "model" or      \
           key == "model name":
            ret += HTML_INDENT + key + ": " + value + "<br>"
        elif key == "cpu MHz":
            ret += HTML_INDENT + key + ": " + value + "<br>"
            break
    return ret
```

Dados de memória foram lidos de `/proc/meminfo`, e os cálculos de uso são os mesmos que os que estão documentados em `man free`.

```python
def mem():
    "For this function, we follow the same calculations as the `free` command"
    lines = read_file("/proc/meminfo").split('\n')
    # MemTotal
    for s in lines[0].split(' '):
        if s.isnumeric():
            total = int(s)
            break
    # MemFree
    for s in lines[1].split(' '):
        if s.isnumeric():
            free = int(s)
            break
    # Buffers
    for s in lines[3].split(' '):
        if s.isnumeric():
            buffers = int(s)
            break
    # Cached
    for s in lines[4].split(' '):
        if s.isnumeric():
            cache = int(s)
            break
    # SReclaimable
    for s in lines[27].split(' '):
        if s.isnumeric():
            cache += int(s)
            break

    used = total - free - buffers - cache
    return "Total: " + str(total) + "Kb, Used: " + str(used) + "Kb"
```

A versão do sistema foi colhida de `/proc/version`:

```python
def sysversion():
    return read_file("/proc/version")
```

Os `PID`s e os nomes dos processos sendo executados na máquina correspondem aos diretórios numerados localizados em `/proc`. Dentro de cada um desses diretórios, há um arquivo `stat`, cuja primeira palavra é o `PID` e a segunda é o comando, entre parênteses:

```python
def proc_list():
    ret = "<br>" + HTML_INDENT + "Pid Name<br>"
    for dir_entry in os.listdir("/proc"):
        if dir_entry.isnumeric():
            s = read_file("/proc/" + dir_entry + "/stat")
            pid = s.split(' ')[0]
            name = s.split(' ')[1].strip("()")
            ret += HTML_INDENT + pid + " " + name + "<br>"
    return ret
```

O uso de cpu é mensurado através dos dados em `/proc/stat`. A documentação encontrada em `man proc` explica que os valores em `/proc/stat` correspondem ao tempo que o cpu permaneceu em cada um de seus estados (includindo `idle`). Usando essas informações, podemos calcular o percentual de tempo em que a cpu ficou ocupada. `/proc/stat` contém informações cumulativas desde que o sistema foi inicializado. Isso significa que para calcularmos os valores atuais, precisamos medir em um determinado instante, aguardar, medir novamente, e pegar a diferença entre os valores. No script, nós medimos a primeira vez durante a inicialização, e medimos novamente cada vez que é feita uma requisição da página para o servidor.

```python
def updt_proc_usage() -> float:
    global prev_idle
    global prev_non_idle
    cpustats = read_file("/proc/stat").split('\n')[0].split(' ')[2:]
    idle = int(cpustats[3]) + int(cpustats[4])  # idle + iowait
    non_idle = int(cpustats[0]) + \
        int(cpustats[1]) +        \
        int(cpustats[2]) +        \
        int(cpustats[5]) +        \
        int(cpustats[6]) +        \
        int(cpustats[7])

    prev_total = prev_idle + prev_non_idle
    total = idle + non_idle

    totald = total - prev_total
    idled = idle - prev_idle

    cpu_percentage = float(totald - idled) / float(totald)

    prev_idle = idle
    prev_non_idle = non_idle

    return cpu_percentage * 100.0
```
