import BaseLayout from "./BaseLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Home, Rocket, Server, Database as DbIcon, Search } from "lucide-react";

export default function IndexPage() {
  return (
    <BaseLayout title="Vite + React + TS" showNavbar={false}>
      <div className="mx-auto max-w-3xl">
        <Card className="border-border">
          <CardHeader className="flex items-center gap-3 text-center">
            <div className="flex gap-3 text-primary">
              <Rocket className="h-6 w-6" />
              <Server className="h-6 w-6" />
            </div>
            <CardTitle className="text-2xl">Vite + React + TS</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-sm text-muted-foreground text-center">
              Point d’entrée de l’interface. Utilise Tailwind + shadcn/ui en thème sombre et des icônes lucide.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Button asChild className="w-full">
                <a href="/">
                  <Home className="mr-2 h-4 w-4" /> Accueil
                </a>
              </Button>
              <Button variant="outline" asChild className="w-full">
                <a href="/">
                  <DbIcon className="mr-2 h-4 w-4" /> Bases
                </a>
              </Button>
              <Button variant="outline" asChild className="w-full">
                <a href="/">
                  <Search className="mr-2 h-4 w-4" /> Rechercher
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </BaseLayout>
  )
}


