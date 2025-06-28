# Azure Pipeline Deployment Instructions for CSV Data Manager

## Overview
This document provides complete instructions for deploying the Streamlit CSV Data Manager application to Azure using Azure DevOps Pipelines.

## Prerequisites

### 1. Azure Resources
- Azure subscription with appropriate permissions
- Azure App Service (Linux, Python 3.11)
- Azure DevOps organization and project

### 2. Service Connections
Create the following service connections in Azure DevOps:
- **Azure Resource Manager** connection to your Azure subscription
- Name it appropriately (e.g., `azure-subscription-connection`)

## Setup Instructions

### Step 1: Create Azure App Service

1. **Create App Service in Azure Portal:**
   ```bash
   # Using Azure CLI (optional)
   az webapp create \
     --resource-group your-resource-group \
     --plan your-app-service-plan \
     --name your-app-name \
     --runtime "PYTHON|3.11" \
     --deployment-local-git
   ```

2. **Configure App Service Settings:**
   - Runtime stack: Python 3.11
   - Operating System: Linux
   - Region: Choose appropriate region
   - Pricing tier: B1 Basic or higher recommended

### Step 2: Configure Azure DevOps Pipeline

1. **Create Variable Group** (Library → Variable groups):
   - Name: `csv-data-manager-variables`
   - Variables:
     ```
     azureServiceConnection: 'your-azure-service-connection-name'
     webAppName: 'your-web-app-name'
     resourceGroupName: 'your-resource-group'
     ```

2. **Update Pipeline Variables** in `azure-pipelines.yml`:
   - Ensure `azureServiceConnection` matches your service connection name
   - Update `webAppName` to match your Azure App Service name

### Step 3: Repository Setup

1. **File Structure** (ensure these files are in your repository):
   ```
   your-repo/
   ├── app.py
   ├── data_manager.py
   ├── utils.py
   ├── deployment_requirements.txt
   ├── azure-pipelines.yml
   ├── Dockerfile
   ├── .streamlit/
   │   └── config.toml
   ├── attached_assets/
   │   └── mapped_quals_1751118898970.csv
   └── DEPLOYMENT_INSTRUCTIONS.md
   ```

2. **Commit and Push** all files to your main/master branch

### Step 4: Create Pipeline in Azure DevOps

1. **Navigate to Pipelines** in your Azure DevOps project
2. **Create New Pipeline:**
   - Choose your repository source (GitHub, Azure Repos, etc.)
   - Select "Existing Azure Pipelines YAML file"
   - Choose `azure-pipelines.yml` from the repository
3. **Review and Run** the pipeline

### Step 5: Configure Environment (if needed)

1. **Create Environment** (Pipelines → Environments):
   - Name: `production`
   - Type: Virtual machines / Kubernetes / None
   - Add approval gates if required

## Application Configuration

### Environment Variables (set in Azure App Service)
```bash
# Required for production
WEBSITE_RUN_FROM_PACKAGE=1
SCM_DO_BUILD_DURING_DEPLOYMENT=true

# Optional: Streamlit specific
STREAMLIT_SERVER_PORT=8000
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
```

### App Service Configuration
- **Startup Command:** `streamlit run app.py --server.port 8000 --server.address 0.0.0.0`
- **Python Version:** 3.11
- **Always On:** Enabled (for production)

## Pipeline Details

### Build Stage
1. Sets up Python 3.11 environment
2. Installs dependencies from `deployment_requirements.txt`
3. Validates imports and basic functionality
4. Creates deployment package
5. Publishes build artifacts

### Deploy Stage
1. Downloads build artifacts
2. Extracts application files
3. Deploys to Azure App Service using Web Deploy
4. Configures startup command for Streamlit

## Key Files Explained

### `deployment_requirements.txt`
Contains Python dependencies:
```
streamlit==1.28.0
pandas==2.1.3
numpy==1.25.2
```

### `.streamlit/config.toml`
Streamlit server configuration:
```toml
[server]
headless = true
address = "0.0.0.0"
port = 8000

[browser]
gatherUsageStats = false
```

### `azure-pipelines.yml`
Complete CI/CD pipeline configuration with:
- Automated builds on main/master branch
- Dependency installation and validation
- Artifact creation and deployment
- Azure App Service deployment

## Troubleshooting

### Common Issues

1. **Build Failures:**
   - Check Python version compatibility
   - Verify all dependencies in `deployment_requirements.txt`
   - Ensure all required files are committed

2. **Deployment Failures:**
   - Verify Azure service connection permissions
   - Check App Service configuration
   - Ensure correct resource group and app name

3. **Runtime Issues:**
   - Check App Service logs in Azure Portal
   - Verify startup command configuration
   - Check environment variables

### Monitoring

1. **Azure Portal:**
   - App Service → Monitoring → Logs
   - Application Insights (if configured)

2. **Pipeline Monitoring:**
   - Azure DevOps → Pipelines → Runs
   - Check build and deployment logs

## Security Considerations

1. **Service Connections:**
   - Use least privilege access
   - Regularly rotate service principal credentials

2. **Environment Variables:**
   - Store sensitive data in Azure Key Vault
   - Reference secrets in App Service configuration

3. **Data Security:**
   - Ensure uploaded CSV files are handled securely
   - Consider data retention policies

## Scaling and Performance

1. **App Service Plan:**
   - Monitor CPU and memory usage
   - Scale up/out based on usage patterns

2. **Application Optimization:**
   - Consider data caching for large CSV files
   - Implement session state management

## Support and Maintenance

1. **Regular Updates:**
   - Keep dependencies updated in `deployment_requirements.txt`
   - Monitor security advisories for Python packages

2. **Backup Strategy:**
   - Regular repository backups
   - App Service backup configuration

---

## Quick Start Commands

```bash
# Clone repository
git clone your-repo-url
cd your-repo

# Test locally
pip install -r deployment_requirements.txt
streamlit run app.py

# Deploy (after pipeline setup)
git add .
git commit -m "Deploy to Azure"
git push origin main
```

For additional support or questions, refer to the Azure DevOps and Streamlit documentation.