# Deploy Keys Setup for Armcalc

## Step 1: Generate SSH Deploy Key on Your Server

Run this command on your server to generate an SSH key:

```bash
# Using ed25519 (recommended - most secure and compact)
ssh-keygen -t ed25519 -C "armcalc-deploy-key" -f ~/.ssh/armcalc_deploy_key -N ""

# Alternative: Using RSA if ed25519 is not supported
ssh-keygen -t rsa -b 4096 -C "armcalc-deploy-key" -f ~/.ssh/armcalc_deploy_key -N ""
```

## Step 2: Display the Public Key

```bash
cat ~/.ssh/armcalc_deploy_key.pub
```

The output will look like one of these formats:
- `ssh-ed25519 AAAA... armcalc-deploy-key`
- `ssh-rsa AAAA... armcalc-deploy-key`

## Step 3: Add Deploy Key to GitHub Repository

1. Go to your repository: https://github.com/armcoincrypto/Armcalc
2. Navigate to **Settings** > **Deploy keys** > **Add deploy key**
3. Enter a **Title** (e.g., "Server Deploy Key")
4. Paste the **public key** (content from step 2)
5. Check **Allow write access** if you need to push changes
6. Click **Add key**

## Step 4: Configure SSH to Use the Deploy Key

Create or edit `~/.ssh/config`:

```bash
cat >> ~/.ssh/config << 'EOF'
Host github.com-armcalc
    HostName github.com
    User git
    IdentityFile ~/.ssh/armcalc_deploy_key
    IdentitiesOnly yes
EOF
```

## Step 5: Clone Using the Deploy Key

```bash
git clone git@github.com-armcalc:armcoincrypto/Armcalc.git
```

Or update existing remote:

```bash
git remote set-url origin git@github.com-armcalc:armcoincrypto/Armcalc.git
```

## Supported Key Types

GitHub accepts these key types for deploy keys:
- `ssh-ed25519` (recommended)
- `ssh-rsa`
- `ecdsa-sha2-nistp256`
- `ecdsa-sha2-nistp384`
- `ecdsa-sha2-nistp521`
- `sk-ecdsa-sha2-nistp256@openssh.com` (security key)
- `sk-ssh-ed25519@openssh.com` (security key)

## Test Connection

```bash
ssh -T git@github.com-armcalc
```

Expected output: "Hi armcoincrypto/Armcalc! You've successfully authenticated..."
