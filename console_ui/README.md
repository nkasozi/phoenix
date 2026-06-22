# Console User interface

This folder contains the web user interface for the console of Phoenix. The console allows users to
configure a specific social media analyses.

## Available Scripts

### Running the development server.

```bash
    npm run dev
```

### Building for production.

```bash
    npm run build
```

### Building a production container

```bash
    docker build -f Dockerfile -t phoenix-console-ui .
```

### Running the production server.

```bash
    npm run start
```

## Environment Variables:

The console UI uses `.env.<environment>` file to initialise the application with the correct config.

Currently there are 4 `.env.<environment>` files in use:

- `.env.example` and example file that can be used as a template for others
- `.env.local`
- `.env.development`
- `.env.production`

### Setup Environment Variables for Local Environment.

To set up environment variables, copy the .env.example file to create a new .env.local file:

```bash
    cp .env.example .env.local
```

### Linting

We have linting that works with pre commit and lint-staged. If you run `npm install` the pre
commit will automatically be installed and run on all staged files in `console_ui/`.

To run a lint check you can use the command:

```bash
  npm run lint
```

## Learn More

To learn more about **Refine**, please check out the [Documentation](https://refine.dev/docs)

- **REST Data Provider** [Docs](https://refine.dev/docs/core/providers/data-provider/#overview)
- **Mantine** [Docs](#)
- **Inferencer** [Docs](https://refine.dev/docs/packages/documentation/inferencer)

## API for development

To get the API (backend) for development you can use the local environment in
`phoenix/python/projects/phiphi/`. To do this:

- start a new shell (terminal)
- follow the commands in `phoenix/python/projects/phiphi/README.md` to start the development
  environment

### Authentication for development API

After running the development API, you can authenticate as a user by setting the appropriate cookie
(phiphi-user-email) with the user's email address. The default email admin@admin.com is
automatically generated in the backend. To authenticate, execute the following JavaScript code in
your browser's console:

```
# Set the user email admin@admin.com is added by default.
document.cookie = "phiphi-user-email=admin@admin.com";

# Check if the correct user is authenticated.
fetch('http://localhost:8080/users/me', {
  method: 'GET',
  credentials: 'include'
})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

The first line of the code sets the user's email in the cookie, while the second line verifies the
authentication status by fetching the user data from the API using the previously set cookie.

## Easy steps for Translation:

Simple way to translate:
Get required items to be translated in the proper json format and simply ask ChatGPT to translate the values (not the keys) to what ever language is required.

Example prompt:

Please translate the values in this JSON from English to <other language>. Check your work.

`/console_ui/public/locales/en/common.json`

## Deploying Your Next.js Project on Vercel:

1. **Login to Vercel:** - Visit [Vercel's website](https://vercel.com/) and log in to your account.

2. **Import Your Next.js Project:** - Once logged in, click on the "Import Project" button on the dashboard.

3. **Choose The Git Repository:** - Select your Next.js project's Git repository from the list.

4. **Configure Deployment Settings:** - Choose the branch you want to deploy from and configure other settings like environment variables.

5. **Deploy The Project:** - Click on the "Deploy" button to start the deployment process.

6. **Monitor Deployment Progress:** - Watch the real-time progress of your deployment on the Vercel dashboard.

7. **Access Your Deployed Application:** - Once deployment is complete, Vercel will provide a unique URL to access your Next.js application.

8. **Automatic Deployment:** - Vercel automatically deploys the application whenever changes are detected in the connected Git repository.

For more detailed instructions, refer to [Vercel's documentation](https://vercel.com/docs).

## Deploying Your Next.js Project on AWS Amplify:

1. **Sign in to AWS Amplify Console:**

- Navigate to the [AWS Amplify Console](https://console.aws.amazon.com/amplify/) and sign in to your AWS account.

2. **Create a New Deployment:**

- Click on the "Connect App" button on the AWS Amplify Console dashboard.
- Choose your Git provider and repository where your Next.js project is hosted.
- Follow the on-screen instructions to connect your repository to AWS Amplify.

3. **Configure Build Settings:**

- AWS Amplify Console will automatically detect your project settings. you can customize the build settings such as the build command:

```bash
    commands:
        - if [ "${AWS_BRANCH}" = "master" ]; then npm run build:prod; fi
```

- Review and confirm the build settings.

4. **Deploy Your Application:**

- Once the build settings are configured, AWS Amplify Console will start the deployment process automatically.
- Monitor the deployment progress on the AWS Amplify Console dashboard.

5. **Access Your Deployed Application:**

- Once the deployment is complete, AWS Amplify Console will provide you with a unique URL where your Next.js application is hosted.
- Click on the provided URL to access your deployed Next.js application.

## Adding a New Gather Type

To add a new gather type, follow the steps below:

1. **Replicate an Existing Gather Type**

- Navigate to the gathers folder path:  
  `console_ui/src/app/projects/[projectid]/gathers/apify_facebook_posts`
- This folder contains 4 subfolders: `[id]`, `create`, `duplicate`, and `edit`.
- Replicate this folder structure to create a new type of gather.

2. **Rename the Folder**

- Rename the replicated folder to the desired new type, e.g., `apify_facebook_comments`.

3. **Edit the `[id]` Folder (View Page)**

- Open the `page.tsx` file located in the `[id]` folder.
- Add/Remove Fields: Modify the form fields as necessary.
- Update Resource Routes: Replace all occurrences of `apify_facebook_posts` with `apify_facebook_comments` or your new gather type.
- Translation:
  - Create the required translation objects in `console_ui/public/locales`.
  - Update the translation paths in `page.tsx` to align with the new gather type.

4. **Edit the Create Page**

a. Replicate a Form Component:

- Go to `console_ui/src/components/forms/gather`.
- Replicate any file and rename it according to your new gather type.
- Update `InitialFormValues` and the `Rules` function to meet the requirements of the new gather type.

b. Update Create Page (`page.tsx`):

- Open the `page.tsx` file in the `create` folder from the replicated folder:  
  `console_ui/src/app/projects/[projectid]/gathers/`.
- Add/Remove fields as needed.
- Update resource routes in the `handleGatherSave` function to match the new gather type, e.g., change:  
  `projects/${projectid}/gathers/apify_facebook_posts` to  
  `projects/${projectid}/gathers/apify_facebook_comments`.

c. Translation:

- Create the necessary translation objects in `console_ui/public/locales`.
- Adjust translation paths in `page.tsx` to match the newly created translation files.

5. **Repeat Same Actions For Edit Page**

6. **Repeat Same Actions For Duplicate Page**

7. **Update Refine Configuration**

- Navigate to the `console_ui/src/app/_refine_context.tsx` file.

- Add the newly created gather type as a resource in Refine. For example:

```javascript
{
  name: "apify_facebook_posts",
  create: "/projects/:projectid/gathers/apify_facebook_posts/create",
  edit: "/projects/:projectid/gathers/apify_facebook_posts/edit/:id",
  show: "/projects/:projectid/gathers/apify_facebook_posts/:id",
  meta: {
    label: "Apify Facebook Posts",
    parent: "projects",
    hide: true,
  },
}

```

## Dependencies updating

To update the dependencies, you can use the following command:

- check the outdated dependencies: `npm outdated`
- update the dependencies: `npm update`

It is also possible to upgrade, major version, of the dependencies manually doing:

- `npm install <package>@latest`

After any updates have been done manual checks should be made.

### Notes on dependencies updating

- tailwindcss: It was not possible to upgrade to higher major version as some of the styling of
  Mantine doesn't work as expected. We think we would need to update Mantine first.
- i18n packages: There are a number of i18n packages which we where able to update and fix build
  bugs. These are on the branch `console_ui/i18n_update`. However there is a very strange run time
  error when you try `npm run dev`. We think this is to do with the fact that we can't update the
  nextjs version.
- nextjs: We require that refine updates to using the newest version of nextjs.
- mantine: We require that refine updates to using the newest version of mantine.
