reStructuredText usage
======================

This documentation is written in ``reStructuredText``. The following are the common syntax elements with examples:

External links
--------------

To create an external link, use the following syntax:

.. code-block:: rst

    `Link text <https://example.com>`_

Link to sections in the documentation
-------------------------------------

To link to a section within the documentation, create a reference at the top of that section using this syntax:

.. code-block:: rst

    .. _section-name:

    Section title
    =============

Then, link to that section using the following syntax:

.. code-block:: rst

    :ref:`section-name`

Headings
--------
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
----------

Separate paragraphs with a blank line without indentation.

Lists
-----

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
-------------

Use the ``.. code-block::`` directive to display multi-line code snippets. Specify the file format or programming language after the directive to turn on proper syntax highlighting. For example:

.. code-block:: rst

    .. code-block:: py

        def hello_world():
            print("Hello, World!")

Inline code
-----------

For short pieces of code within a sentence, use double **backticks (``)**. This helps distinguish the code from regular text. For example:

.. code-block:: rst

    Use the ``print()`` function to display output.

Tables
------

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
