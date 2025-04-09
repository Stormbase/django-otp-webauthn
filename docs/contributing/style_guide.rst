.. _`style-guide`:

Style guide
===========

This documentation follows the `Google Developer Documentation Style Guide <https://developers.google.com/style>`_.

Apart from the style guide, here are some additional guidelines to follow when writing documentation for Django OTP WebAuthn:

Spelling
--------

Use American English spelling. For example:

* color, not colour

* optimize, not optimise

* canceled, not cancelled

Words to avoid
--------------

Avoid informal, unclear words, and internet slangs. Use the following table for guidance:

+----------+----------------+---------------------+
| Word     | Meaning        | Use instead         |
+==========+================+=====================+
| ain’t    | is not         | isn’t               |
+----------+----------------+---------------------+
| gonna    | going to       | going to            |
+----------+----------------+---------------------+
| gotta    | got to         | have to             |
+----------+----------------+---------------------+
| how’d    | how did /      | how did / how would |
|          | how would      |                     |
+----------+----------------+---------------------+
| how’ll   | how will       | how will            |
+----------+----------------+---------------------+
| I’d      | I would        | I would             |
+----------+----------------+---------------------+
| may’ve   | may have       | may have            |
+----------+----------------+---------------------+
| mayn’t   | may not        | may not             |
+----------+----------------+---------------------+
| might’ve | might have     | might have          |
+----------+----------------+---------------------+
| mightn’t | might not      | might not           |
+----------+----------------+---------------------+
| ’twas    | it was         | it was              |
+----------+----------------+---------------------+
| wanna    | want to        | want to             |
+----------+----------------+---------------------+
| YMMV     | Your mileage   | Your mileage may    |
|          | may vary       | vary                |
+----------+----------------+---------------------+
| u need to| you need to    | you need to         |
| download | download       | download            |
| Python   | Python         | Python              |
+----------+----------------+---------------------+

Commonly misused words and preferred alternatives
-------------------------------------------------

The following table shows the commonly misused words and their preferred alternatives:

+----------------+---------------------------------------------------------+
| Avoid          | Use instead                                             |
+================+=========================================================+
| cons           | disadvantages                                           |
+----------------+---------------------------------------------------------+
| desire, desired|  want or need                                           |
+----------------+---------------------------------------------------------+
| does not yet   | doesn’t                                                 |
+----------------+---------------------------------------------------------+
| enable         | Be precise by using **turn on** for features or         |
|                | **lets you** for capabilities                           |
+----------------+---------------------------------------------------------+
| pros           | advantages                                              |
+----------------+---------------------------------------------------------+
| leverage       | use **build on**, **use**, or **take advantage of**     |
|                | if needed                                               +
+----------------+---------------------------------------------------------+

Latin phrases and abbreviations
-------------------------------

Avoid Latin phrases like *ergo* or *de facto* and abbreviations like *i.e.* or *e.g.* Use clear, common English phrases instead. If possible, find a simpler way to express the idea. The only exception is *etc.*, which is acceptable when space is limited:

+------------+-----------------------+
| Avoid      | Use  instead          |
+============+=======================+
| e.g.       | for example, such as  |
+------------+-----------------------+
| i.e.       | that is               |
+------------+-----------------------+
| viz.       | namely                |
+------------+-----------------------+
| ergo       | therefore             |
+------------+-----------------------+

.. _`lists`:

Lists
-----

You can use lists to organize information in the documentation. There are two types of list:

Numbered lists
~~~~~~~~~~~~~~

Use numbered lists for step-by-step instructions when order matters. For example:

1. Install the necessary software.

2. Configure the settings.

3. Run the application.

Unnumbered lists
~~~~~~~~~~~~~~~~

Use bullet lists for items that do not follow a specific order. For example:

* Features included in the latest update

* Supported file formats

* Common error messages

Avoid overly complex nesting in lists. If a list becomes too deep, consider breaking it into smaller sections. Ensure all items in a list follow the same grammatical structure to maintain clarity.

reStructuredText usage
----------------------

This documentation is written in ``reStructuredText``. The following are the common syntax elements with examples:

External links
~~~~~~~~~~~~~~

To create an external link, use the following syntax:

.. code-block:: rst

    `Link text <https://example.com>`_

Link to sections in the documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To link to a section within the documentation, create a reference at the top of that section using this syntax:

.. code-block:: rst

    .. _section-name:

    Section title
    =============

Then, link to that section using the following syntax:

.. code-block:: rst

    :ref:`section-name`

Headings
~~~~~~~~
Ensure your headings are concise and descriptive. Use sentence case for headings by capitalizing only the first word. If a heading includes an official term, retain its original capitalization.

Also, use heading levels in sequential order without skipping. For example, progress from H1 to H2 to H3. Avoid using headings beyond H3. Instead, structure content with numbered or bullet lists.

Also, underlines must be the same length as the title or heading. Use sentence case for headings by capitalizing only the first word:

1. Heading one (H1):

.. code-block:: rst

    Heading one - page title
    ========================

2. Heading two (H2):

.. code-block:: rst

    Heading two - section title
    ---------------------------

3. Heading three (H3):

.. code-block:: rst

    Heading three - major subsection
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Paragraphs
~~~~~~~~~~

Separate paragraphs with a blank line without indentation.

Lists
~~~~~

Lists can be numbered or unnumbered. For more information, see :ref:`lists`. You can also nest them to create different hierarchy levels:

1. **Unnumbered lists:** To create an unordered list, start each item with an **asterisk (*)** followed by a space. Ensure that there is a blank line between the items and before and after the list:

    .. code-block:: rst

        * Item 1

        * Item 2

        * Item 3

2. **Numbered lists:** To create an ordered list, start each item with a number followed by a period and a space. Ensure that there is a blank line between the items and before and after the list:

    .. code-block:: rst

        1. Item 1

        2. Item 2

        3. Item 3

3. **Nested lists:** For nested unnumbered lists, indent each sub-item level using four spaces. Use the same asterisk (`*`) syntax for all levels. Also, ensure that there's a blank line between the items and before and after the list:

    .. code-block:: rst

        * Item 1
            * Sub-item 1
            * Sub-item 2

        * Item 2
            * Sub-item 1
            * Sub-item 2

Code snippets
~~~~~~~~~~~~~

Use the ``.. code-block::`` directive to display multi-line code snippets. Specify the file format or programming language after the directive to turn on proper syntax highlighting. For example:

.. code-block:: rst

    .. code-block:: py

        def hello_world():
            print("Hello, World!")

Inline code
~~~~~~~~~~~

For short pieces of code within a sentence, use double **backticks (``)**. This helps distinguish the code from regular text. For example:

.. code-block:: rst

    Use the ``print()`` function to display output.

Tables
~~~~~~

You can choose to use either grid tables or simple tables. Each type has its own syntax and use cases:

1. **Grid tables:** Grid tables give you full control over the layout and structure of your table. You create them by manually drawing the cell grid using characters like **+**, **-**, and **|**.

    Here’s an example of a grid table:

    .. code-block:: rst

        +-----------------+-----------------+
        | Header 1        | Header 2        |
        +=================+=================+
        | Row 1, Column 1 | Row 1, Column 2 |
        +-----------------+-----------------+
        | Row 2, Column 1 | Row 2, Column 2 |
        +-----------------+-----------------+

2. **Simple tables:** Simple tables are easier to create but come with some limitations. They require at least two rows, and the cells in the first column cannot span multiple lines.

    Here’s an example of a simple table:

    .. code-block:: rst

        ===============  ===============
        Header 1         Header 2
        ===============  ===============
        Row 1, Column 1  Row 1, Column 2
        Row 2, Column 1  Row 2, Column 2
        ===============  ===============
