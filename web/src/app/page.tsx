import { CtaBand } from "@/components/landing/cta-band";
import { Hero } from "@/components/landing/hero";
import { ModelGallery } from "@/components/landing/model-gallery";
import { ResultStrip } from "@/components/landing/result-strip";
import { Thesis } from "@/components/landing/thesis";
import { defaultScenario } from "@/lib/api/scenario";
import { dateOnly } from "@/lib/format";

export default function Home() {
  const { frontier } = defaultScenario;
  const prov = frontier.provenance;

  return (
    <>
      <Hero
        frontier={frontier}
        dataStart={dateOnly(prov.data_start)}
        dataEnd={dateOnly(prov.data_end)}
      />
      <ResultStrip />
      <Thesis />
      <ModelGallery />
      <CtaBand />
    </>
  );
}
