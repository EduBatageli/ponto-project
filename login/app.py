from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

# Melhorar responsividade
# desabilitar botoes 
# levar info de horas para o banco 


app = Flask(__name__)
app.secret_key = "segredo"

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
db = SQLAlchemy(app)


# configurando o banco de dados
class UsuarioCadastrado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)    
    user = db.Column(db.String(50), unique=True, nullable=False)    
    password = db.Column(db.String(250), nullable=False)

# Criar a tabela se não existir
def criar_banco():
    with app.app_context():
        db.create_all()
        print("Banco de dados criado com sucesso.")

# Chame a função para criar o banco de dados
criar_banco()

@app.route("/")
def paginaLogin():
    return render_template("index.html")

@app.route("/home", methods=["GET","POST"])
def home():
    if "email" in session:
        nome = session["email"]  # Recupera o email da sessão
        
    hora_atual = datetime.now().strftime('%H:%M:%S')  # Formata a hora no formato HH:MM:SS
    
    # Inicializa as horas na sessão se não existirem
    if "hora_entrada" not in session:
        session["hora_entrada"] = None
    if "hora_saida_almoco" not in session:
        session["hora_saida_almoco"] = None
    if "hora_retorno_almoco" not in session:
        session["hora_retorno_almoco"] = None
    if "hora_saida" not in session:
        session["hora_saida"] = None
    if request.method == "POST" or request.method == "GET":
        
        periodo = request.form.get("periodo")
        
        if periodo == "entrada":
            session["hora_entrada"] = hora_atual
            
        elif periodo == "saida_almoco":
            session["hora_saida_almoco"] = hora_atual
            
        elif periodo == "retorno_almoco":
            session["hora_retorno_almoco"] = hora_atual
            
        elif periodo == "saida":
            session["hora_saida"] = hora_atual
            
        # Converte as horas de string para objetos datetime
        hora_format = "%H:%M:%S"
        hora_entrada = datetime.strptime(session["hora_entrada"], hora_format)
        hora_saida_almoco = datetime.strptime(session["hora_saida_almoco"], hora_format)
        hora_retorno_almoco = datetime.strptime(session["hora_retorno_almoco"], hora_format)
        hora_saida = datetime.strptime(session["hora_saida"], hora_format)

        print(session["hora_entrada"])

        tempo_trabalhado = (hora_saida - hora_entrada) - (hora_retorno_almoco - hora_saida_almoco)
        horas_contratadas = timedelta(hours=8)


        # Calcula o banco de horas (diferença entre horas trabalhadas e horas contratadas)
        banco_de_horas = tempo_trabalhado - horas_contratadas
        total_segundos = banco_de_horas.total_seconds()
        
        # Converte segundos para horas 
        horas_banco = total_segundos // 3600
        
        # Exibe o resultado (agora sem arredondamento incorreto)
        print(f"Banco de horas: {horas_banco}")
        
        return render_template("ponto.html", nome=nome, hora_atual=hora_atual,
                           hora_entrada=session["hora_entrada"], hora_saida_almoco=session["hora_saida_almoco"],
                           hora_retorno_almoco=session["hora_retorno_almoco"], hora_saida=session["hora_saida"], horas_trabalhadas=tempo_trabalhado, banco=horas_banco)
    else:
        return redirect(url_for("paginaLogin"))  # Se não há sessão, redireciona para login

@app.route("/login", methods=["GET","POST"])
def login():
    email = request.form["email"]
    senha = request.form["password"]
    
    if not email or not senha:
        flash("O email e a senha são obrigatórios.", "error")
        return redirect(url_for("paginaLogin"))
           
    # Buscar o usuário no banco de dados
    usuario = UsuarioCadastrado.query.filter_by(email=email).first()
     # Verifica se o usuário foi encontrado
    if not usuario:
        flash("usuário não cadastrado", "error")
        return redirect(url_for("paginaLogin"))
    if usuario.password != senha:
        flash("Senha incorreta", "error")
        return redirect(url_for("paginaLogin"))
    else:
        #criar validação de usuário
        session["email"] = email
        return redirect(url_for("home"))

# criando botao de logout e evita que um usuário entre direto no home
@app.route("/logout", methods=["GET","POST"])
def logout():
    session.pop("email", None)
    return redirect(url_for("paginaLogin"))

# criando rota para cadastrar o novo usuário
@app.route("/cadastrar")
def cadastroUsuario():
    return render_template("cadastrarUsuario.html")

#faz toda a validacao do cadastro
@app.route("/Validarcadastro", methods=["GET","POST"])
def validarCadastro():
    nome = request.form["nome"]
    email = request.form["email"]
    senha = request.form["password"]
    senha2 = request.form["password2"]
    
    if senha != senha2:
        flash("As senhas não coincidem, tente novamente.", "error")
        return redirect(url_for("cadastroUsuario"))
    elif not email or not senha:
        flash("O email e a senha são obrigatórios.", "error")
        return redirect(url_for("cadastroUsuario"))
    else:
        # Verificar se o email já está cadastrado
        if UsuarioCadastrado.query.filter_by(email=email).first():
            flash("Este email já está cadastrado.", "error")
            return redirect(url_for("cadastroUsuario"))
        else:
            # adiciona novo usuário
            novo_usuario = UsuarioCadastrado(user=nome, email=email, password=senha)
            db.session.add(novo_usuario)
            db.session.commit()
        

        # adicionar mensagem de cadastro
        return redirect(url_for("paginaLogin"))
     

if __name__ == "__main__":
    app.run(debug=True)