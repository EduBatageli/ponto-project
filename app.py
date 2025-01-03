from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = "segredo"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
db = SQLAlchemy(app) 

class UsuarioCadastrado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)    
    user = db.Column(db.String(50), unique=True, nullable=False)    
    password = db.Column(db.String(250), nullable=False)
    tipoUsuario = db.Column(db.String(20), nullable=False)
    
class PontoUsuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)  
    data = db.Column(db.String(250), unique=True, nullable=False)   
    entrada = db.Column(db.Integer, unique=True, nullable=False)    
    saida_almoco = db.Column(db.Integer, nullable=False)
    volta_almoco = db.Column(db.Integer, nullable=False)
    saida = db.Column(db.Integer, nullable=False)
    


# Criar a tabela se não existir
def criar_banco():
    with app.app_context():
        db.create_all()
        print("Banco de dados criado com sucesso.")

# Chame a função para criar o banco de dados
criar_banco()


# Decorador para verificar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página', 'error')
            return redirect(url_for('paginaLogin'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================================================================================================

# tela login

"""
DADOS FALTANTES:

- trabalhar o backend da parte de ADM
- arrumar horas do backend
- criar banco dass horas

"""

@app.route("/")
def paginaLogin():
    return render_template("index.html")

@app.route("/validarLogin", methods=("GET", "POST")) 
def validarLogin():
    email_user = request.form["email"]
    senha_user = request.form["password"]
    usuario = UsuarioCadastrado.query.filter_by(email=email_user).first()
    
    if not usuario:
        flash("Usuário não encontrado. Verifique seu email.", "error")
        return redirect(url_for("paginaLogin"))
    
    else:
        if usuario.password == senha_user:
            # Adicionar informações do usuário na sessão
            session['user_id'] = usuario.id
            session['user_name'] = usuario.user
            return redirect(url_for("home", nome=usuario.user))
        
        else:
            flash("Senha incorreta", "error")
            return redirect(url_for("paginaLogin"))


@app.route("/loginADM")
def loginADM():
    return render_template("loginADM.html")


@app.route("/validarLoginADM", methods=("GET", "POST"))
def validarLoginADM():
    email_user = request.form["email"]
    senha_user = request.form["password"]
    usuario = UsuarioCadastrado.query.filter_by(email=email_user).first()
    
    if not usuario:
        flash("Usuário não encontrado. Verifique seu email.", "error")
        return redirect(url_for("paginaLogin"))
    
    else:

        if usuario.password == senha_user and usuario.tipoUsuario == "ADM":
            # Adicionar informações do usuário na sessão
            session['user_id'] = usuario.id
            session['user_name'] = usuario.user
            session["user_type"] = "ADM"
            return redirect(url_for("adm", nome=usuario.user))
        
        elif usuario.tipoUsuario != "ADM":
            flash("Login somente para ADM", "error")
            return redirect(url_for("paginaLogin"))
        
        else:
            flash("Senha incorreta", "error")
            return redirect(url_for("loginADM"))


# tela ADM  

@app.route("/adm")
def adm():
    # Verifica se existe um usuário logado e se é ADM
    if 'user_id' not in session:
        flash('Por favor, faça login como ADM', 'error')
        return redirect(url_for('loginADM'))
        
    if session.get('user_type') != 'ADM': 
        flash('Acesso não autorizado', 'error')
        return redirect(url_for('paginaLogin'))
        
    return render_template("painelADM.html", nome=session.get("user_name"))
      
@app.route("/cadastrar")
def paginaCadastro():
    # habilitar 
    # if 'user_id' not in session:
    #     flash('Por favor, faça login como ADM', 'error')
    #     return redirect(url_for("loginADM"))
        
    # if session.get('user_type') != 'ADM': 
    #     flash('Acesso não autorizado', 'error')
    #     return redirect(url_for("loginADM"))
    
    return render_template("cadastrarUsuario.html")

@app.route("/validarCadastro", methods=("POST", "GET"))
def validarCadastro():
    nome = request.form["nome"]
    email_user = request.form["email"]
    senha = request.form["password"]
    senha2 = request.form["password2"]
    tipoUser = request.form["tipoUser"]
    
    if senha != senha2:
        flash("As senhas não coincidem, tente novamente.", "error")
        return redirect(url_for("validarCadastro"))
        
    elif len(senha) < 8 or len(senha2) < 8:
        flash("As senhas tem menos de 8 digitos", "error")
        return redirect(url_for("validarCadastro"))
        
    elif not email_user or not senha:
        flash("O email e a senha são obrigatórios.", "error")
        return redirect(url_for("validarCadastro"))
    
    elif UsuarioCadastrado.query.filter_by(email=email_user).first():
        flash("Este email já está cadastrado.", "error")
        return redirect(url_for("paginaLogin"))
    
    else:
        # Criar novo usuário
        novo_usuario = UsuarioCadastrado(email=email_user, user=nome, password=senha, tipoUsuario=tipoUser)
        db.session.add(novo_usuario)
        db.session.commit()
        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for("paginaLogin"))

# ambas telas

current_date = datetime.now().strftime('%d/%m/%y')

horas_trabalhadas = ""

@app.route("/home/<nome>")
@login_required
def home(nome):

    if nome != session['user_name']:
        flash('Acesso não autorizado', 'error')
        return redirect(url_for('home', nome=session['user_name']))
    
    return render_template("ponto.html", nome=nome, data_atual=current_date)

lista_horarios = []

@app.route('/horas', methods=['POST'])
def registrar_horas():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    if "entrada" in data and data["entrada"].strip():
        lista_horarios.append(data["entrada"].strip())
        # print(lista_horarios)
    
    if "saida_almoco" in data and data["saida_almoco"].strip():
        lista_horarios.append(data["saida_almoco"].strip())
        # print(lista_horarios)
    
    if "volta_almoco" in data and data["volta_almoco"].strip():
        lista_horarios.append(data["volta_almoco"].strip())
        # print(lista_horarios)
    
    if "saida" in data and data["saida"].strip():
        lista_horarios.append(data["saida"].strip())
        # print(lista_horarios)
        
    print(f"lista: {lista_horarios}")

    #add ao banco aqui

        
    if len(lista_horarios) >= 4:
        print(f"tamanho {len(lista_horarios)}")
        lista_horarios.clear()
        


    return jsonify({'message': 'Horário registrado com sucesso!'})




    

# executar a cada 10 min
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('paginaLogin'))

if __name__ == "__main__":
    app.run(debug=True)