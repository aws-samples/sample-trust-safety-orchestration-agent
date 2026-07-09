const steps = [
  {
    number: '1',
    title: 'Prerequisites',
    content: [
      'AWS CLI v2 configured with credentials',
      'AWS SAM CLI v1.90+',
      'uv (auto-installed by setup.sh if missing)',
      'Node.js 20+ and npm',
    ],
  },
  {
    number: '2',
    title: 'Clone the repository',
    code: `git clone https://github.com/aws-samples/sample-trust-safety-orchestration-agent.git
cd trust-safety-orchestration-agent`,
  },
  {
    number: '3',
    title: 'Install dependencies and build',
    code: './setup.sh',
  },
  {
    number: '4',
    title: 'Deploy the backend',
    description: 'For staging/dev (no VPC or Redis — faster deploy):',
    code: 'sam deploy --guided --parameter-overrides "UseRedis=false Environment=dev"',
    note: 'Save the outputs printed at the end — you will need RestApiUrl, WebSocketUrl, FrontendBucketName, and CloudFrontDistributionId.',
  },
  {
    number: '5',
    title: 'Configure the frontend',
    description: 'From the project root:',
    code: `cd frontend
cp .env.example .env.production`,
    afterDescription: 'Edit .env.production and set the values from your SAM deploy outputs:',
    afterCode: `VITE_API_BASE_URL=https://<your-api-id>.execute-api.<region>.amazonaws.com/<env>/api/v1
VITE_WS_URL=wss://<your-ws-id>.execute-api.<region>.amazonaws.com/<env>`,
  },
  {
    number: '6',
    title: 'Build and deploy the frontend',
    code: `npm run build
aws s3 sync dist/ s3://<your-frontend-bucket>/ --delete
aws cloudfront create-invalidation --distribution-id <your-distribution-id> --paths "/*"`,
  },
  {
    number: '7',
    title: 'Create a login user',
    description: 'Create an admin user in your Cognito User Pool:',
    code: `aws cognito-idp admin-create-user \\
  --user-pool-id <your-user-pool-id> \\
  --username admin \\
  --user-attributes Name=custom:role,Value=admin \\
  --temporary-password 'TempPass123!'

aws cognito-idp admin-set-user-password \\
  --user-pool-id <your-user-pool-id> \\
  --username admin \\
  --password 'YourSecurePassword!' \\
  --permanent`,
  },
  {
    number: '8',
    title: 'Access your app',
    description: 'Open your CloudFront URL and log in with the credentials you created. The dashboard will display in demo mode until live data flows through Kinesis.',
  },
]

function CodeBlock({ code }: { code: string }) {
  return (
    <pre className="mt-2 overflow-x-auto rounded-lg bg-gray-900 p-4 text-sm text-gray-100">
      <code>{code}</code>
    </pre>
  )
}

export function GettingStartedPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-8 p-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Getting Started</h1>
        <p className="mt-2 text-gray-600">
          Deploy the Trust &amp; Safety Orchestration Agent to your AWS account and get the dashboard running.
        </p>
      </div>

      <div className="space-y-6">
        {steps.map((step) => (
          <div key={step.number} className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="flex items-start gap-4">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-indigo-600 text-sm font-bold text-white">
                {step.number}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">{step.title}</h3>
                {step.description && (
                  <p className="mt-1 text-sm text-gray-600">{step.description}</p>
                )}
                {step.content && (
                  <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-gray-700">
                    {step.content.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                )}
                {step.code && <CodeBlock code={step.code} />}
                {step.afterDescription && (
                  <p className="mt-3 text-sm text-gray-600">{step.afterDescription}</p>
                )}
                {step.afterCode && <CodeBlock code={step.afterCode} />}
                {step.note && (
                  <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                    <strong>Note:</strong> {step.note}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-green-200 bg-green-50 p-6">
        <h3 className="font-semibold text-green-900">Production deployment</h3>
        <p className="mt-1 text-sm text-green-800">
          For production, deploy with <code className="rounded bg-green-100 px-1.5 py-0.5 text-xs">UseRedis=true</code> (the default) to include VPC, ElastiCache Redis, and security groups. Set <code className="rounded bg-green-100 px-1.5 py-0.5 text-xs">Environment=prod</code> and configure your platform API URLs when prompted.
        </p>
      </div>
    </div>
  )
}
