import { createClient } from "@hey-api/openapi-ts"
import path from "path"
import fs from "fs/promises"

async function generateMicroserviceClients() {
  const OPENAPI_DIR = "./openapi"
  const OUTPUT_BASE = "./src/client"

  try {
    const files = await fs.readdir(OPENAPI_DIR)
    const openapiFiles = files.filter(file => file.endsWith(".json"))

    console.log(`Found ${openapiFiles.length} OpenAPI specifications`)

    for (const file of openapiFiles) {
      const input = path.join(OPENAPI_DIR, file)
      const serviceName = path.basename(file, ".json")
      const output = path.join(OUTPUT_BASE, serviceName)

      console.log(`Generating client for [${serviceName}]...`)

      await createClient({
        input,
        output,
        client: "legacy/axios",
        plugins: [
          {
            name: "@hey-api/sdk",
            asClass: true,
            operationId: true,
            methodNameBuilder: (operation) => {
              let name = operation.name
              const service = operation.service

              if (service && name.toLowerCase().startsWith(service.toLowerCase())) {
                name = name.slice(service.length)
              }

              return name.charAt(0).toLowerCase() + name.slice(1)
            },
          },
        ],
      })

      console.log(`Client for [${serviceName}] generated successfully`)
    }

    console.log("Successfully generated clients.")
  } catch (error) {
    console.error("Error generating clients:", error)
    process.exit(1)
  }
}

generateMicroserviceClients()
