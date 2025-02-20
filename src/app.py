"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planets, Favorites

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

# USERS
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.serialize() for user in users]), 200

# FAVORITES: Endpoints para cualquier usuario

# Listar todos los favoritos de un usuario dado
@app.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Usuario no encontrado"}), 404
    # Se asume que en el modelo User tienes definida la relación "favorites"
    favorites = [fav.serialize() for fav in user.favorites]
    return jsonify(favorites), 200

# PEOPLE
@app.route('/people', methods=['GET'])
def get_people():
    people = People.query.all()
    return jsonify([person.serialize() for person in people]), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = People.query.get(people_id)
    if not person:
        return jsonify({"message": "Character not found"}), 404
    return jsonify(person.serialize()), 200

# PLANETS
@app.route('/planets', methods=['GET'])
def get_planets():
    planets = Planets.query.all()
    return jsonify([planet.serialize() for planet in planets]), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planets.query.get(planet_id)
    if not planet:
        return jsonify({"message": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200

# FAVORITES Endpoints

# Añadir un nuevo favorito de planeta para un usuario específico
@app.route('/users/<int:user_id>/favorites/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(user_id, planet_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Usuario no encontrado"}), 404
    planet = Planets.query.get(planet_id)
    if not planet:
        return jsonify({"message": "Planeta no encontrado"}), 404

    # Verificar si el favorito ya existe
    existing_fav = Favorites.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if existing_fav:
        return jsonify({"message": "El planeta ya está en favoritos"}), 400

    new_fav = Favorites(user_id=user_id, planet_id=planet_id)
    db.session.add(new_fav)
    db.session.commit()
    return jsonify({"message": "Planeta agregado a favoritos"}), 201

# Añadir un nuevo favorito de personaje para un usuario específico
@app.route('/users/<int:user_id>/favorites/people/<int:people_id>', methods=['POST'])
def add_favorite_people(user_id, people_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Usuario no encontrado"}), 404
    person = People.query.get(people_id)
    if not person:
        return jsonify({"message": "Personaje no encontrado"}), 404

    # Verificar si el favorito ya existe
    existing_fav = Favorites.query.filter_by(user_id=user_id, people_id=people_id).first()
    if existing_fav:
        return jsonify({"message": "El personaje ya está en favoritos"}), 400

    new_fav = Favorites(user_id=user_id, people_id=people_id)
    db.session.add(new_fav)
    db.session.commit()
    return jsonify({"message": "Personaje agregado a favoritos"}), 201

# Eliminar favorito de planeta para un usuario específico
@app.route('/users/<int:user_id>/favorites/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(user_id, planet_id):
    favorite = Favorites.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if not favorite:
        return jsonify({"message": "Favorito no encontrado"}), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "Planeta eliminado de favoritos"}), 200

# Eliminar favorito de personaje para un usuario específico
@app.route('/users/<int:user_id>/favorites/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_people(user_id, people_id):
    favorite = Favorites.query.filter_by(user_id=user_id, people_id=people_id).first()
    if not favorite:
        return jsonify({"message": "Favorito no encontrado"}), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "Personaje eliminado de favoritos"}), 200

# This only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
