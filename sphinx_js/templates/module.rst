{% import 'common.rst' as common %}

{{ name }}
================================================================================

.. js:module:: {{ name }}

{% if description -%}
    **Description:** {{ description }}
{%- endif %}

{% if authors -%}
    **Author(s):**  {% for a in authors -%}
                        {% if loop.last -%}{{ a }}{% else %}{{ a }}, {% endif %}
                    {%- endfor %}
{%- endif %}

{% if version -%}
    **Version:** {{ version }}
{%- endif %}

{% if license_information -%}
    **License:** {{ license_information }}
{%- endif %}

{% if members -%}
    {{ members|indent(3) }}
{%- endif %}
