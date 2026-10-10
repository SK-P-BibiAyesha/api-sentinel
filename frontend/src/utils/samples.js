// Pre-packaged OpenAPI sample specifications for quick demo & testing

export const CONTACTS_OLD_JSON = `openapi: 3.0.3
info:
  title: Contact Details API
  version: "1.0.0"

paths:
  /api/v1/contacts/{id}:
    get:
      summary: Get contact details
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: Contact details
          content:
            application/json:
              schema:
                type: object
                required:
                  - id
                  - name
                  - email
                properties:
                  id:
                    type: integer
                    example: 101
                  name:
                    type: string
                    example: "Rahul Kumar"
                  email:
                    type: string
                    format: email
                    example: "rahul@example.com"
                  phone:
                    type: string
                    example: "+91-9000000001"
                  age:
                    type: integer
                    example: 24
                  address:
                    type: string
                    example: "Guntur, Andhra Pradesh"
        "404":
          description: Contact not found
`;

export const CONTACTS_NEW_JSON = `openapi: 3.0.3
info:
  title: Contact Details API
  version: "2.0.0"

paths:
  /api/v1/contacts/{id}:
    get:
      summary: Get updated contact details
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: Updated contact details
          content:
            application/json:
              schema:
                type: object
                required:
                  - id
                  - full_name
                  - email
                  - phone
                properties:
                  id:
                    type: integer
                    example: 101
                  full_name:
                    type: string
                    example: "Rahul Kumar"
                  email:
                    type: string
                    format: email
                    example: "rahul@example.com"
                  phone:
                    type: integer
                    example: 9000000001
                  age:
                    type: string
                    example: "24"
                  address:
                    type: string
                    example: "Guntur, Andhra Pradesh"
                  date_of_birth:
                    type: string
                    format: date
                    example: "2002-05-15"
        "404":
          description: Contact not found
`;

export const PRODUCTS_OLD_YAML = `openapi: 3.0.3
info:
  title: Product Service API
  version: 1.0.0

paths:
  /products:
    get:
      summary: Get all products
      responses:
        "200":
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  productName:
                    type: string
                  price:
                    type: number
                  category:
                    type: string

  /products/{id}:
    get:
      summary: Get a product by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: Product found
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: integer
                  productName:
                    type: string
                  price:
                    type: number
`;

export const PRODUCTS_NEW_YAML = `openapi: 3.0.3
info:
  title: Product Service API
  version: 2.0.0

paths:
  /products:
    get:
      summary: Get all products
      responses:
        "200":
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  name:
                    type: string
                  price:
                    type: string
                  category:
                    type: string
                  stock:
                    type: integer

  /products/{id}:
    get:
      summary: Get a product by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: Product found
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  price:
                    type: string
`;

export function createSampleFiles(type = "contacts") {
  if (type === "products") {
    const oldFile = new File([PRODUCTS_OLD_YAML], "products-v1.yaml", {
      type: "application/x-yaml",
    });
    const newFile = new File([PRODUCTS_NEW_YAML], "products-v2.yaml", {
      type: "application/x-yaml",
    });
    return { oldFile, newFile, label: "Product Service API (YAML)" };
  }

  const oldFile = new File([CONTACTS_OLD_JSON], "contacts-v1.json", {
    type: "application/json",
  });
  const newFile = new File([CONTACTS_NEW_JSON], "contacts-v2.json", {
    type: "application/json",
  });
  return { oldFile, newFile, label: "Contacts API (JSON)" };
}

