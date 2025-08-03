// React import not needed for JSX in React 17+
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-3xl">Welcome to Tana Helper</CardTitle>
          <CardDescription>
            Your companion tool for working with Tana data exports and API integrations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-foreground">
          <p>
            One of the great things about Tana is that it is able to call external systems via the{' '}
            <a
              href="https://tana.inc/docs/command-nodes#make-api-request"
              className="text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              <code className="bg-muted px-1 py-0.5 rounded">Make API request</code>
            </a>{' '}
            command. Not only can it make calls to internet services with APIs to fetch data into
            Tana, you can also pass existing Tana node data to these APIs and then receive results
            in return. The results of these calls can be added as new Tana nodes or can be used as
            input to further features like the built-in AI integration.
          </p>

          <p>
            This service, <strong>Tana Helper</strong>, is designed to be called from Tana, but it
            also has a simple web UI for exploring and testing.
          </p>

          <p>
            The service can process JSON exports from Tana and then transform the resulting data
            into various formats. This includes conversion to formats like Mermaid for diagram
            generation, data structures for visualization, and integration with AI services for
            analysis.
          </p>

          <div className="mt-6 p-4 bg-muted rounded-lg">
            <h3 className="font-semibold mb-2">Available Features:</h3>
            <ul className="space-y-1 text-sm">
              <li>
                •{' '}
                <Link to="/visualizer" className="text-primary hover:underline">
                  Graph Visualization
                </Link>{' '}
                - Interactive 2D/3D network graphs
              </li>
              <li>
                •{' '}
                <Link to="/diagram" className="text-primary hover:underline">
                  Class Diagrams
                </Link>{' '}
                - Generate Mermaid diagrams from your data
              </li>
              <li>
                •{' '}
                <Link to="/ragindex" className="text-primary hover:underline">
                  RAG Index
                </Link>{' '}
                - AI-powered search and analysis
              </li>
              <li>
                •{' '}
                <Link to="/api" className="text-primary hover:underline">
                  API Documentation
                </Link>{' '}
                - Explore the REST API
              </li>
              <li>
                •{' '}
                <Link to="/configure" className="text-primary hover:underline">
                  Configuration
                </Link>{' '}
                - Set up API keys and preferences
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
