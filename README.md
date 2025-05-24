# Structured Output Generator

Convert any query to a structured JSON format by using only natural language.

### Setting Up

1. Clone this repository

```
git clone https://github.com/purusharthmalik/structured-output-generator.git
cd structured-output-generator
```

2. Create a new environment and install the dependencies

```
pip install uv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

3. Set the `GROQ_API_KEY` in the `.env` file.

4. Start the application

```
python src/main.py
```

> ![NOTE]
> The application will be started at `http://127.0.0.1:7860` by default.

### Agent Workflow

- The initial user query is classified into one of the pre-defined categories.
- If the category is "Other", a function is called that retrieves URLs from Google.
- Otherwise the initial query is used to fill the pre-defined fields for a particular category.
- User is prompted questions till all the fields are filled.
<img src="/images/workflow.png" height="600">

### Interface Description

![initial screen](/images/init_screen.png)

### Example Runs

- For `Dining` category,
![dining](/images/dining_test.png)

- For `Travel` category,
![travel](/images/travel_test.png)

- For `Gifting` category,
![gifting](/images/gifting_test.png)

- For `Cab Booking` category,
![cab booking](/images/cab_booking_test.png)

- For `Other` category,
![other](/images/other_test.png)

More details about the sample runs can be found in the [sample document](sample_doc.md).
