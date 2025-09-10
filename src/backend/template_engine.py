"""
Système de templates simple pour GenEWeb
Remplacement léger de Jinja2 pour éviter les dépendances
"""

import os
import re
from typing import Any, Dict, Optional


class TemplateError(Exception):
    """Exception pour les erreurs de template."""


class TemplateEngine:
    """
    Moteur de templates simple pour GenEWeb.

    Ce moteur gère les directives de base comme {% extends %}, {% block %},
    {% if %}, {% for %} et les variables {{ var }}.

    Attributes:
        template_dir: Répertoire contenant les templates
        _cache: Cache des templates compilés
    """

    def __init__(self, template_dir: str) -> None:
        """
        Initialiser le moteur de templates.

        Args:
            template_dir: Chemin vers le répertoire des templates
        """
        self.template_dir: str = template_dir
        self._cache: Dict[str, str] = {}

    def render(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Rendre un template avec un contexte donné.

        Args:
            template_name: Nom du fichier template
            context: Variables à injecter dans le template

        Returns:
            HTML rendu

        Raises:
            FileNotFoundError: Si le template n'existe pas
            TemplateError: Si erreur de syntaxe dans le template
        """
        if context is None:
            context: dict[str, str] = {}

        template_content = self._load_template(template_name)
        return self._render_template(template_content, context)

    def _load_template(self, template_name: str) -> str:
        """
        Charger un template depuis le disque.

        Args:
            template_name: Nom du template à charger

        Returns:
            Contenu du template

        Raises:
            FileNotFoundError: Si le template n'existe pas
        """
        if template_name in self._cache:
            return self._cache[template_name]

        template_path = os.path.join(self.template_dir, template_name)

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_name}")

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            raise TemplateError(f"Error reading template {template_name}: {e}")

        # Traiter l'héritage de templates
        content = self._process_extends(content)

        self._cache[template_name] = content
        return content

    def _process_extends(self, content: str) -> str:
        """
        Traiter les directives {% extends %}.

        Args:
            content: Contenu du template

        Returns:
            Contenu avec héritage résolu
        """
        extends_match = re.search(r'{%\s*extends\s+["\']([^"\']+)["\']\s*%}', content)

        if extends_match:
            parent_template = extends_match.group(1)
            parent_content = self._load_template(parent_template)

            # Supprimer la directive extends
            content = re.sub(r'{%\s*extends\s+["\'][^"\']+["\']\s*%}', "", content)

            # Traiter les blocs
            content = self._merge_blocks(parent_content, content)

        return content

    def _merge_blocks(self, parent: str, child: str) -> str:
        """
        Fusionner les blocs parent et enfant.

        Args:
            parent: Contenu du template parent
            child: Contenu du template enfant

        Returns:
            Template avec les blocs fusionnés
        """
        # Extraire tous les blocs du template enfant
        child_blocks: dict[str, str] = {}
        block_pattern = r"{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}"

        for match in re.finditer(block_pattern, child, re.DOTALL):
            block_name = match.group(1)
            block_content = match.group(2).strip()
            child_blocks[block_name] = block_content

        # Remplacer les blocs dans le parent
        def replace_block(match):
            block_name = match.group(1)
            default_content = match.group(2)

            if block_name in child_blocks:
                return child_blocks[block_name]
            else:
                return default_content

        result = re.sub(block_pattern, replace_block, parent, flags=re.DOTALL)
        return result

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Rendre un template avec les variables.

        Args:
            template: Contenu du template
            context: Variables du contexte

        Returns:
            Template rendu avec les variables substituées
        """
        result = template

        # Variables simples {{ variable }}
        def replace_var(match):
            var_expr = match.group(1).strip()
            return str(self._resolve_variable(var_expr, context))

        result = re.sub(r"{{\s*([^}]+)\s*}}", replace_var, result)

        # Conditions simples {% if %}
        result = self._process_conditions(result, context)

        # Boucles simples {% for %}
        result = self._process_loops(result, context)

        # Inclusions {% include %}
        result = self._process_includes(result, context)

        # Supprimer les blocs non traités
        result = re.sub(r"{%\s*set\s+[^%]*%}", "", result)
        result = re.sub(r"{%\s*block\s+\w+\s*%}", "", result)
        result = re.sub(r"{%\s*endblock\s*%}", "", result)

        return result

    def _resolve_variable(self, var_expr: str, context: Dict[str, Any]) -> Any:
        """Résoudre une expression de variable"""
        # Filtres simples
        if "|" in var_expr:
            var_name, filter_name = var_expr.split("|", 1)
            var_name = var_name.strip()
            filter_name = filter_name.strip()

            value = self._get_nested_value(var_name, context)
            return self._apply_filter(value, filter_name)

        return self._get_nested_value(var_expr, context)

    def _get_nested_value(self, path: str, context: Dict[str, Any]) -> Any:
        """Obtenir une valeur imbriquée comme 'object.property'"""
        if "." in path:
            parts = path.split(".")
            value = context.get(parts[0], "")

            for part in parts[1:]:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict):
                    value = value.get(part, "")
                else:
                    return ""
            return value

        return context.get(path, "")

    def _apply_filter(self, value: Any, filter_name: str) -> str:
        """Appliquer un filtre à une valeur"""
        if filter_name == "escape":
            return self._escape_html(str(value))
        elif filter_name == "number_format":
            try:
                return f"{int(value):,}".replace(",", " ")
            except (ValueError, TypeError):
                return str(value)
        elif filter_name == "date_to_string":
            # Supposons que nous avons une méthode sur l'objet date
            if hasattr(value, "to_string"):
                return value.to_string()
            return str(value)
        elif filter_name == "length":
            try:
                return str(len(value))
            except TypeError:
                return "0"

        return str(value)

    def _escape_html(self, text: str) -> str:
        """Échapper le HTML"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def _process_conditions(self, template: str, context: Dict[str, Any]) -> str:
        """Traiter les conditions {% if %}"""
        pattern = r"{%\s*if\s+([^%]+)%}(.*?)(?:{%\s*else\s*%}(.*?))?{%\s*endif\s*%}"

        def replace_condition(match):
            condition = match.group(1).strip()
            if_content = match.group(2)
            else_content = match.group(3) if match.group(3) else ""

            if self._evaluate_condition(condition, context):
                return if_content
            else:
                return else_content

        return re.sub(pattern, replace_condition, template, flags=re.DOTALL)

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Évaluer une condition simple"""
        # Conditions simples
        if " == " in condition:
            left, right = condition.split(" == ", 1)
            left_val = self._resolve_variable(left.strip(), context)
            right_val = (
                right.strip().strip("\"'")
                if right.strip().startswith('"') or right.strip().startswith("'")
                else self._resolve_variable(right.strip(), context)
            )
            return str(left_val) == str(right_val)

        if " != " in condition:
            left, right = condition.split(" != ", 1)
            left_val = self._resolve_variable(left.strip(), context)
            right_val = (
                right.strip().strip("\"'")
                if right.strip().startswith('"') or right.strip().startswith("'")
                else self._resolve_variable(right.strip(), context)
            )
            return str(left_val) != str(right_val)

        if condition.startswith("not "):
            var = condition[4:].strip()
            value = self._resolve_variable(var, context)
            return not bool(value)

        # Variable simple
        value = self._resolve_variable(condition, context)
        return bool(value)

    def _process_loops(self, template: str, context: Dict[str, Any]) -> str:
        """Traiter les boucles {% for %}"""
        pattern = r"{%\s*for\s+(\w+)\s+in\s+([^%]+)%}(.*?){%\s*endfor\s*%}"

        def replace_loop(match):
            loop_var = match.group(1).strip()
            iterable_expr = match.group(2).strip()
            loop_content = match.group(3)

            iterable = self._resolve_variable(iterable_expr, context)
            if not iterable:
                return ""

            result: list[str] = []
            for item in iterable:
                loop_context = context.copy()
                loop_context[loop_var] = item
                rendered_content = self._render_template(loop_content, loop_context)
                result.append(rendered_content)

            return "".join(result)

        return re.sub(pattern, replace_loop, template, flags=re.DOTALL)

    def _process_includes(self, template: str, context: Dict[str, Any]) -> str:
        """Traiter les inclusions {% include %}"""
        pattern = r'{%\s*include\s+["\']([^"\']+)["\']\s*%}'

        def replace_include(match):
            include_template = match.group(1)
            try:
                included_content = self._load_template(include_template)
                return self._render_template(included_content, context)
            except FileNotFoundError:
                return f"<!-- Template not found: {include_template} -->"

        return re.sub(pattern, replace_include, template)


# Instance globale du moteur de templates
template_engine = None


def get_template_engine():
    """Obtenir l'instance du moteur de templates"""
    global template_engine
    if template_engine is None:
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        template_engine = TemplateEngine(template_dir)
    return template_engine


def render_template(template_name: str, **context) -> str:
    """Fonction utilitaire pour rendre un template"""
    engine = get_template_engine()
    return engine.render(template_name, context)
