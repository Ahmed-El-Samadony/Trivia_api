import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start =  (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  

  #Set up CORS. Allow '*' for origins.
  CORS(app, resources={r"/*": {"origins": "*"}})


  #Use the after_request decorator to set Access-Control-Allow
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,DELETE')
    return response


  #Create an endpoint to handle GET requests for all available categories.
  @app.route('/categories', methods= ['GET'])
  def catgories():
    selection = Category.query.all()
    formatted_categories = [category.format() for category in selection]
    catgories = {}
    for category in formatted_categories:
      catgories[category['id']] = category['type']

    if (catgories):
      return jsonify({
        'success': True,

        'categories': catgories,
      })
    else:
      abort(404)


  #Create an endpoint to handle GET requests for questions, including pagination (every 10 questions). 
  @app.route('/questions')
  def questions():
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)

    if len(current_questions) == 0:
      abort(404)
    
    formatted_categories = [category.format() for category in Category.query.all()]
    catgories = {}
    for category in formatted_categories:
      catgories[category['id']] = category['type']

    return jsonify({
        'success': True,
        
        'questions': current_questions,
        'total_questions': len(Question.query.all()),
        'categories': catgories,
        'current_category': None,
      })

  #Create an endpoint to POST a new question,
  #Create a POST endpoint to get questions based on a search term.
  # 
  # There are two request URLs in the frontend having the same path and method. Instead of modifying the frontend, I created one endpoint here that handles both of them and it worked. 
  @app.route('/questions', methods = ['POST'])
  def search_or_submit_question():
    body = request.get_json()

    try:
      searchTerm = body.get('searchTerm', '')
      if (searchTerm != ''):
        selection = Question.query.filter(Question.question.ilike(f'%{searchTerm}%'))
        current_questions = paginate_questions(request, selection)

        return jsonify({
          'success': True,
          
          'questions': current_questions,
          'total_questions': len(current_questions),
          'current_category': None,
        })
      else:
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
        question.insert()

        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
          'success': True,
          'created': question.id,
          'questions': current_questions,
          })
    except:
      abort(422)


  #Create an endpoint to DELETE question using a question ID. 
  @app.route('/questions/<int:question_id>', methods= ['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)

      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'deleted': question_id,
      })
    except:
      abort(422)

  
  #Create a GET endpoint to get questions based on category. 
  @app.route('/categories/<int:category_id>/questions', methods= ['GET'])
  def get_questions_by_category(category_id):
    category = Category.query.get(category_id)
    if (category):
      selection = Question.query.filter(Question.category == category_id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
          'success': True,
          
          'questions': current_questions,
          'total_questions': len(current_questions),
          'current_category': Category.query.get(category_id).format(),
        })
    else:
      abort(404)


  #Create a POST endpoint to get questions to play the quiz. 
  @app.route('/quizzes', methods=['POST'])
  def play_quiz():
    try:
      body = request.get_json()
      
      previous_questions = body.get('previous_questions',[])
      quiz_category = body.get('quiz_category', '')

      #The frontend handles pushing the new question to previous_questions, formatting and evaluating the answer whether right or wrong, calculating the score and determining when to stop the quiz. 
      # so we only need to return a random question that is not in the previous questions and within the selected category if any.

      category_id = quiz_category['id']
      if category_id == 0: #default value in the frontend that indicates all categories
        selection = Question.query.filter(Question.id.notin_(previous_questions)).all()
      else:
        selection = Question.query.filter(Question.category == category_id, Question.id.notin_(previous_questions)).all()

      if (selection):
        question = random.choice(selection).format()
      else:
        question = None

      return jsonify({
          'success': True,
          'question': question,
        })
      
    except:
      abort(422) 

  # Create error handlers for all expected errors 
  @app.errorhandler(400)
  def bad_request(error):
    return jsonify ({
      'success': False,
      'error': 400,
      'message': 'Bad Request'
    }), 400

    @app.errorhandler(404)
    def not_found(error):
      return jsonify ({
        'success': False,
        'error': 404,
        'message': 'Resource Not Found'
      }), 404

    @app.errorhandler(422)
    def unprocessable_entity(error):
      return jsonify ({
        'success': False,
        'error': 422,
        'message': 'Not Processable'
      }), 422
  
  return app

    