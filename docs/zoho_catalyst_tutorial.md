# Zoho Catalyst Tutorial

You can build different microservices using different languages (like Node.js and Python) within the same Catalyst project. AppSail is designed for this "polyglot" approach.

AppSail is a Platform-as-a-Service (PaaS). This means you simply provide your source code, and **Zoho Catalyst handles all the containerization, deployment, and scaling for you** behind the scenes. It's one of the biggest advantages of using AppSail—it simplifies the process so you can focus only on your code.

-----

## Beginner's Tutorial: Hosting Node.js and Python Microservices

Here’s a step-by-step guide to building and deploying a Node.js "Users Service" and a Python "Orders Service" together, served by a single API Gateway.

### Prerequisites

  * A Zoho account and a new, empty Catalyst project.
  * **Node.js** and **npm** installed.
  * **Python** and **pip** installed.
  * The **Catalyst CLI** installed and logged in (`catalyst login`).

-----

### Step 1: Set Up the Project Monorepo

We'll use a single repository (a "monorepo") to hold both services.

1.  On your computer, create a main project folder.

2.  Open your terminal, navigate into that folder, and run `catalyst init`:

    ```bash
    mkdir my-polyglot-project
    cd my-polyglot-project
    catalyst init
    ```

3.  Follow the prompts to associate this folder with your new project in the Catalyst cloud.

-----

### Step 2: Create the Node.js Microservice

Let's build the "Users Service" first.

1.  **From the root `my-polyglot-project` directory**, create a folder for the service:
    ```bash
    mkdir users-service
    cd users-service
    ```
2.  Initialize a Node.js project and install the `express` web framework:
    ```bash
    npm init -y
    npm install express
    ```
3.  Inside the `users-service` folder, create a file named `server.js` and add this code:
    ```javascript
    // users-service/server.js
    const express = require('express');
    const app = express();
    const port = process.env.PORT || 9000;

    app.get('/users', (req, res) => {
        res.json({
            language: 'JavaScript (Node.js)',
            service: 'Users Service',
            data: [{ id: 1, name: 'Alice' }, { id: 2, name: 'Bob' }]
        });
    });

    app.listen(port, () => {
        console.log(`Node.js Users Service started on port: ${port}`);
    });
    ```
4.  Navigate back to the project root: `cd ..`

-----

### Step 3: Create the Python Microservice 🐍

Now, let's create the "Orders Service" using Python and the Flask framework.

1.  **From the root `my-polyglot-project` directory**, create a folder for the new service:

    ```bash
    mkdir orders-service
    cd orders-service
    ```

2.  Inside the `orders-service` folder, create a file named `main.py` and add this code:

    ```python
    # orders-service/main.py
    import os
    from flask import Flask, jsonify

    app = Flask(__name__)

    @app.route('/orders')
    def get_orders():
        return jsonify(
            language='Python',
            service='Orders Service',
            data=[
                {'id': 1001, 'item': 'Laptop', 'quantity': 1},
                {'id': 1002, 'item': 'Mouse', 'quantity': 2}
            ]
        )

    if __name__ == '__main__':
        port = int(os.environ.get('PORT', 9000))
        app.run(host='0.0.0.0', port=port)
    ```

3.  Next, create a file named `requirements.txt`. This file tells Catalyst which Python libraries your service needs. Add the following lines:

    ```text
    # orders-service/requirements.txt
    Flask
    gunicorn
    ```

    **Note:** **Gunicorn** is a production-grade web server that Catalyst uses to run your Flask application efficiently. It's required for Python apps on AppSail.

4.  Navigate back to the project root: `cd ..`

-----

### Step 4: Configure AppSail for Both Services

This is where we tell Catalyst about our two different services and their technology stacks.

1.  **In the root `my-polyglot-project` directory**, create a file named `catalyst-app-config.json`.

2.  Add the following configuration. This is the key step for the polyglot setup.

    ```json
    {
      "apps": [
        {
          "name": "users_service_nodejs",
          "folder": "./users-service",
          "stack": "node18"
        },
        {
          "name": "orders_service_python",
          "folder": "./orders-service",
          "stack": "python3.9"
        }
      ]
    }
    ```

    This configuration clearly defines:

      * An app named `users_service_nodejs`, located in the `users-service` folder, which runs on the **Node.js 18** stack.
      * An app named `orders_service_python`, located in the `orders-service` folder, which runs on the **Python 3.9** stack.

-----

### Step 5: Configure the API Gateway

Now we set up the public URLs and route them to the correct service.

1.  Open the `catalyst-cli-config.json` file located in your project root.

2.  Find the `"api"` section and replace it with this configuration:

    ```json
    {
      "name": "api",
      "memory": 256,
      "targets": [
        {
          "path": "/users",
          "app": "users_service_nodejs",
          "method": "GET"
        },
        {
          "path": "/orders",
          "app": "orders_service_python",
          "method": "GET"
        }
      ]
    }
    ```

    This tells the gateway:

      * Any GET request to `/users` should be sent to our Node.js app.
      * Any GET request to `/orders` should be sent to our Python app.

-----

### Step 6: Deploy the Project 🚀

With everything configured, the deployment is a single command.

1.  Make sure you are in the root `my-polyglot-project` directory in your terminal.
2.  Run the deploy command:
    ```bash
    catalyst deploy
    ```
    Catalyst will read all your configuration files, see that you have one Node.js app and one Python app, build them both correctly, and set up the API Gateway routing.

-----

### Step 7: Test Your Live Endpoints

After deployment finishes, go to your Catalyst Console.

1.  Navigate to **Amplify \> API Gateway** to find your base URL.
2.  **Test the Node.js Service:**
    In your browser, go to `https://<your-project-url>/api/users`. You should see:
    ```json
    { "language": "JavaScript (Node.js)", "service": "Users Service", "data": [...] }
    ```
3.  **Test the Python Service:**
    In your browser, go to `https://<your-project-url>/api/orders`. You should see:
    ```json
    { "language": "Python", "service": "Orders Service", "data": [...] }
    ```

You have now successfully deployed a polyglot microservice architecture on Zoho Catalyst without ever touching a Docker file\!