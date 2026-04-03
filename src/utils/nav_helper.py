from src.models.ModeloCategoria import ModeloCategoria

def get_nav_data():
    return ModeloCategoria.get_all_categories()