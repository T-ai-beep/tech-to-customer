"use client"

import { TrendingUp } from "lucide-react"
import { Bar, BarChart, CartesianGrid, XAxis } from "recharts"

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"

export type ChartDataPoint = {
  name: string;
  [key: string]: string | number;
};

export type GraphProps = {
  title?: string;
  description?: string;
  chartData: ChartDataPoint[];
  dataKey: string; // e.g., "desktop" or "jobsCompleted"
  footerText?: string;
  trendingUp?: boolean;
  trendingPercent?: number;
};

export function ChartBarDefault({
  title = "Bar Chart",
  description = "Data visualization",
  chartData,
  dataKey,
  footerText = "Showing data",
  trendingUp = true,
  trendingPercent = 5.2,
}: GraphProps) {
  const chartConfig: ChartConfig = {
    [dataKey]: {
      label: dataKey.charAt(0).toUpperCase() + dataKey.slice(1),
      color: "var(--color-accent)",
    },
  };

  return (
    <Card className="border-none shadow-none p-0 mt-2 flex flex-col bg-green-300/10">
      <CardHeader>
        <CardTitle className="text-2xl font-bold">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="bg-green-300/30">
        <ChartContainer config={chartConfig}>
          <BarChart accessibilityLayer data={chartData}>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="name "
              tickLine={false}
              tickMargin={10}
              axisLine={false}
            />
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent hideLabel />}
            />
            <Bar dataKey={dataKey} fill="var(--color-accent)" radius={8} />
          </BarChart>
        </ChartContainer>
      </CardContent>
      <CardFooter className="bg-red-300/10">
        <div className="flex gap-2 leading-none font-medium">
          {trendingUp ? "Trending up" : "Trending down"} by {trendingPercent}%{" "}
          <TrendingUp className="h-4 w-4" />
        </div>
        <div className="text-muted-foreground leading-none">{footerText}</div>
      </CardFooter>
    </Card>
  )
}
