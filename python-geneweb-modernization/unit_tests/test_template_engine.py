import os
import tempfile
import pytest
from template_engine import TemplateEngine, render_template, get_template_engine


@pytest.fixture
def temp_template_dir():
    """Créer un dossier temporaire pour stocker les templates"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def engine(temp_template_dir):
    """Instancier le moteur de templates avec le dossier temporaire"""
    return TemplateEngine(temp_template_dir)


def write_template(directory, name, content):
    """Écrire un fichier template dans le répertoire"""
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def test_render_simple_variable(engine, temp_template_dir):
    write_template(temp_template_dir, "hello.html", "Hello {{ name }}!")
    result = engine.render("hello.html", {"name": "Rémi"})
    assert result == "Hello Rémi!"


def test_render_variable_with_filter_escape(engine, temp_template_dir):
    write_template(temp_template_dir, "escape.html", "Safe: {{ value|escape }}")
    result = engine.render("escape.html", {"value": "<b>bold</b>"})
    assert result == "Safe: &lt;b&gt;bold&lt;/b&gt;"


def test_render_condition_if_else(engine, temp_template_dir):
    write_template(
        temp_template_dir,
        "cond.html",
        "{% if is_admin %}Admin{% else %}User{% endif %}"
    )
    assert engine.render("cond.html", {"is_admin": True}) == "Admin"
    assert engine.render("cond.html", {"is_admin": False}) == "User"


def test_include_template(engine, temp_template_dir):
    write_template(temp_template_dir, "child.html", "Child")
    write_template(temp_template_dir, "parent.html", "Start {% include 'child.html' %} End")
    result = engine.render("parent.html")
    assert result == "Start Child End"


def test_include_missing_template(engine, temp_template_dir):
    write_template(temp_template_dir, "main.html", "Here {% include 'missing.html' %}")
    result = engine.render("main.html")
    assert "Template not found: missing.html" in result


def test_extends_and_block(engine, temp_template_dir):
    write_template(
        temp_template_dir,
        "base.html",
        "Header {% block content %}Default{% endblock %} Footer"
    )
    write_template(
        temp_template_dir,
        "child.html",
        '{% extends "base.html" %}{% block content %}Child{% endblock %}'
    )
    result = engine.render("child.html")
    assert result == "Header Child Footer"


def test_nested_value_access(engine, temp_template_dir):
    class User:
        def __init__(self, name):
            self.name = name
    
    write_template(temp_template_dir, "user.html", "User: {{ user.name }}")
    result = engine.render("user.html", {"user": User("Alice")})
    assert result == "User: Alice"


def test_get_template_engine_singleton():
    engine1 = get_template_engine()
    engine2 = get_template_engine()
    assert engine1 is engine2


def test_render_template_helper(temp_template_dir, monkeypatch):
    monkeypatch.setattr("template_engine.get_template_engine", lambda: TemplateEngine(temp_template_dir))
    write_template(temp_template_dir, "helper.html", "Hello {{ who }}")
    result = render_template("helper.html", who="World")
    assert result == "Hello World"
