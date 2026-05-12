<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Controle de SAC - Neon Comercial</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Urbanist:wght@700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        /* RESET E CONFIGURAÇÕES GERAIS */
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            background-color: #0b0f19; 
            color: #e2e8f0; 
            font-family: 'Inter', sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
            padding: 20px;
        }

        /* CONTAINER PRINCIPAL - PAISAGEM (HD) */
        .dashboard {
            width: 1600px;
            height: 900px;
            background-color: #0f172a;
            border-radius: 16px;
            border: 1px solid #1e293b;
            display: flex;
            flex-direction: column;
            padding: 20px 25px;
            gap: 15px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            overflow: hidden;
        }

        /* 1. TOPO: BRANDING E KPIS GERAIS */
        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 12px;
            height: 60px;
        }
        .branding h1 { font-family: 'Urbanist', sans-serif; font-size: 24px; color: #f8fafc; letter-spacing: 1px; }
        .branding span { color: #00f2fe; font-size: 12px; display: block; font-weight: 500; text-transform: uppercase; letter-spacing: 2px; }
        
        .kpi-container { display: flex; gap: 15px; align-items: center; }
        .kpi-box { 
            background: #1e293b; 
            border-left: 4px solid #334155; 
            padding: 8px 16px; 
            border-radius: 6px; 
            text-align: center; 
            display: flex;
            gap: 12px;
            align-items: center;
        }
        .kpi-box.active { border-color: #00f2fe; background: rgba(0, 242, 254, 0.05); }
        .kpi-box.warning { border-color: #f59e0b; background: rgba(245, 158, 11, 0.05); }
        .kpi-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 600; text-align: left;}
        .kpi-value { font-size: 22px; font-weight: 700; color: #f8fafc; }

        .period-selector { 
            background: #0b0f19; 
            border: 1px solid #334155; 
            padding: 8px 14px; 
            border-radius: 6px; 
            font-size: 12px; 
            color: #00f2fe; 
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* 2. METADE SUPERIOR: GRÁFICOS, EQUIPE E REGRAS GUT */
        .upper-grid {
            display: grid;
            grid-template-columns: 2fr 1fr 1.2fr;
            gap: 15px;
            height: 260px;
        }

        .card {
            background: #131c31;
            border-radius: 10px;
            border: 1px solid #1e293b;
            padding: 15px;
            display: flex;
            flex-direction: column;
        }
        .card-title { font-size: 12px; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;}
        .card-title i { color: #00f2fe; }

        /* Gráfico Simulado via SVG + CSS */
        .chart-area { flex-grow: 1; display: flex; flex-direction: column; justify-content: flex-end; position: relative; }
        .chart-svg { width: 100%; height: 160px; overflow: visible; }
        .line-chart { fill: none; stroke: #a3e635; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
        .chart-labels { display: flex; justify-content: space-between; font-size: 9px; color: #64748b; margin-top: 5px; }
        .chart-grid-line { stroke: #1e293b; stroke-width: 1; stroke-dasharray: 4 4; }

        /* Lista de Colaboradores Compacta */
        .team-list { display: flex; flex-direction: column; gap: 6px; overflow-y: auto; flex-grow: 1; padding-right: 5px;}
        .team-row { display: flex; justify-content: space-between; align-items: center; background: rgba(15, 23, 42, 0.5); padding: 5px 10px; border-radius: 4px; font-size: 11px; }
        .team-row span { color: #cbd5e1; }
        .badge-count { background: #334155; color: #00f2fe; font-weight: 700; padding: 2px 6px; border-radius: 4px; font-size: 10px; }

        /* Aba de Regras GUT Simples */
        .rules-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 10px; overflow-y: auto; }
        .rule-group { background: rgba(11, 15, 25, 0.6); padding: 8px; border-radius: 6px; border: 1px solid #1e293b; }
        .rule-group h4 { color: #a3e635; margin-bottom: 5px; font-size: 10px; border-bottom: 1px solid #1e293b; padding-bottom: 3px;}
        .rule-item { display: flex; justify-content: space-between; color: #94a3b8; margin-bottom: 3px; font-size: 9px; }
        .rule-item b { color: #f8fafc; }

        /* 3. METADE INFERIOR: AS DUAS TABELAS LADO A LADO */
        .lower-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            flex-grow: 1;
            height: calc(100% - 350px);
        }

        .table-container {
            background: #131c31;
            border-radius: 10px;
            border: 1px solid #1e293b;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .table-header-bar {
            background: #1e293b;
            padding: 10px 15px;
            font-size: 12px;
            font-weight: 700;
            color: #f8fafc;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #334155;
        }
        .table-header-bar.accent { border-left: 4px solid #00f2fe; }
        .table-header-bar.history { border-left: 4px solid #a3e635; }

        .table-scroll { overflow-y: auto; flex-grow: 1; }
        
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 11px; }
        thead th { 
            position: sticky; 
            top: 0; 
            background: #0f172a; 
            color: #64748b; 
            font-size: 9px; 
            text-transform: uppercase; 
            padding: 8px 12px; 
            border-bottom: 1px solid #334155;
            z-index: 10;
        }
        tbody tr { border-bottom: 1px solid #1e293b; }
        tbody tr:hover { background: rgba(30, 41, 59, 0.5); }
        td { padding: 10px 12px; color: #cbd5e1; vertical-align: middle; }
        
        .client-col { font-weight: 600; color: #f8fafc; }
        .category-tag { font-size: 9px; padding: 2px 6px; border-radius: 4px; background: #334155; font-weight: 500; }
        .category-tag.estrategico { background: rgba(163, 230, 53, 0.15); color: #a3e635; border: 1px solid rgba(163, 230, 53, 0.3); }
        .category-tag.grande { background: rgba(0, 242, 254, 0.15); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.3); }

        .gut-score { font-size: 12px; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-align: center; display: inline-block; min-width: 35px;}
        .gut-score.danger { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #f87171; }
        .gut-score.warning { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #fbbf24; }

        /* CUSTOM SCROLLBARS */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
    </style>
</head>
<body>

<div class="dashboard">
    <div class="top-bar">
        <div class="branding">
            <h1>NEON COMERCIAL</h1>
            <span>Controle Operacional de SAC</span>
        </div>
        <div class="kpi-container">
            <div class="kpi-box active">
                <div class="kpi-label">Total de SAC's<br><span style="font-size:9px;color:#64748b;font-weight:400;">No Período</span></div>
                <div class="kpi-value">9</div>
            </div>
            <div class="kpi-box warning">
                <div class="kpi-label">Em Tratamento<br><span style="font-size:9px;color:#f59e0b;font-weight:400;">Pendentes</span></div>
                <div class="kpi-value" style="color:#f59e0b;">3</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">Finalizados<br><span style="font-size:9px;color:#64748b;font-weight:400;">Concluídos</span></div>
                <div class="kpi-value" style="color:#94a3b8;">6</div>
            </div>
            <div class="period-selector">
                <i class="fa-solid fa-calendar-days"></i>
                <span>1 de abr de 2026 - 30 de abr de 2026</span>
            </div>
        </div>
    </div>

    <div class="upper-grid">
        <div class="card">
            <div class="card-title">
                <span>Acompanhamento de Causas Classificadas (Jan/25 - Mai/26)</span>
                <i class="fa-solid fa-chart-line"></i>
            </div>
            <div class="chart-area">
                <svg class="chart-svg" viewBox="0 0 600 140">
                    <line x1="0" y1="20" x2="600" y2="20" class="chart-grid-line" />
                    <line x1="0" y1="70" x2="600" y2="70" class="chart-grid-line" />
                    <line x1="0" y1="120" x2="600" y2="120" class="chart-grid-line" />
                    <path class="line-chart" d="M 10 90 L 50 60 L 90 55 L 130 60 L 170 30 L 210 80 L 250 35 L 290 85 L 330 70 L 370 75 L 410 75 L 450 55 L 490 90 L 530 20 L 570 90 L 595 120" />
                    <circle cx="530" cy="20" r="4" fill="#00f2fe" />
                    <text x="520" y="12" fill="#00f2fe" font-size="9" font-weight="bold">Pico (18)</text>
                </svg>
                <div class="chart-labels">
                    <span>Jan/25</span><span>Mar</span><span>Mai</span><span>Jul</span><span>Set</span><span>Nov</span><span>Jan/26</span><span style="color:#00f2fe;font-weight:bold;">Fev (Pico)</span><span>Abr</span><span>Mai/26</span>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">
                <span>Colaborador (Procedentes)</span>
                <span style="font-size:10px;color:#64748b;font-weight:500;">Distr. Categoria</span>
            </div>
            <div class="team-list">
                <div class="team-row"><span>Josiane Silva</span><span class="badge-count">3</span></div>
                <div class="team-row"><span>Graziela Sales</span><span class="badge-count">2</span></div>
                <div class="team-row"><span>Mariana Calixto</span><span class="badge-count">2</span></div>
                <div class="team-row"><span>Vitor Clemente</span><span class="badge-count">1</span></div>
                <div class="team-row"><span>Ana Fernandes</span><span class="badge-count">1</span></div>
                <div class="team-row"><span>Julia Moraes</span><span class="badge-count">1</span></div>
                <div class="team-row"><span>Greice Costa</span><span class="badge-count">1</span></div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">
                <span>Critérios Matriz GUT</span>
                <i class="fa-solid fa-circle-info"></i>
            </div>
            <div class="rules-grid">
                <div class="rule-group">
                    <h4>Score Faturamento</h4>
                    <div class="rule-item"><span>> 30M (VIP)</span><b>7</b></div>
                    <div class="rule-item"><span>15M - 30M (Estrat.)</span><b>6</b></div>
                    <div class="rule-item"><span>5M - 15M (M. Gde)</span><b>5</b></div>
                    <div class="rule-item"><span>1M - 5M (Gde)</span><b>4</b></div>
                    <div class="rule-item"><span>< 1M (Méd/Peq)</span><b>1-3</b></div>
                </div>
                <div class="rule-item" style="display:block;">
                    <div class="rule-group" style="margin-bottom:6px;">
                        <h4>Reincidência</h4>
                        <div class="rule-item"><span>> 40 SACs</span><b>5</b></div>
                        <div class="rule-item"><span>15 a 40</span><b>4</b></div>
                        <div class="rule-item"><span>6 a 15</span><b>3</b></div>
                    </div>
                    <div class="rule-group">
                        <h4>Tempo</h4>
                        <div class="rule-item"><span>Até 7 dias</span><b>4</b></div>
                        <div class="rule-item"><span>Até 30 dias</span><b>3</b></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="lower-grid">
        
        <div class="table-container">
            <div class="table-header-bar accent">
                <span>1. DETALHAMENTO DO PERÍODO SELECIONADO (ABRIL 2026)</span>
                <span style="font-size:10px;color:#94a3b8;font-weight:500;">Mostrando 1-9 registros</span>
            </div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>Data</th>
                            <th>Razão Social</th>
                            <th>Cat.</th>
                            <th>Colaborador</th>
                            <th>Causa / Não Conformidade</th>
                            <th style="text-align:center;">GUT</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="white-space:nowrap;color:#64748b;">15/04/2026</td>
                            <td class="client-col">Lanali Laboratorio de Analises SS</td>
                            <td><span class="category-tag estrategico">Estratégico</span></td>
                            <td>Mariana Calixto</td>
                            <td>Cliente solicitou Ciclohexano e enviamos Ciclohexanona</td>
                            <td><span class="gut-score danger">216</span></td>
                        </tr>
                        <tr>
                            <td style="white-space:nowrap;color:#64748b;">23/04/2026</td>
                            <td class="client-col">Sucocitrico Cutrale Ltda</td>
                            <td><span class="category-tag grande">Grande</span></td>
                            <td>Mariana Calixto</td>
                            <td>Liberado a pedido com preço divergente que o cliente havia cotado</td>
                            <td><span class="gut-score danger">192</span></td>
                        </tr>
                        <tr>
                            <td style="white-space:nowrap;color:#64748b;">17/04/2026</td>
                            <td class="client-col">Cargill Agricola SA</td>
                            <td><span class="category-tag grande">Grande</span></td>
                            <td>Josiane Silva</td>
                            <td>Ordem de compras indicava outro fornecedor, pedido foi recusado</td>
                            <td><span class="gut-score warning">48</span></td>
                        </tr>
                        <tr>
                            <td style="white-space:nowrap;color:#64748b;">13/04/2026</td>
                            <td class="client-col">Laborsolo do Brasil SA</td>
                            <td><span class="category-tag">M. Grande</span></td>
                            <td>Vitor Clemente</td>
                            <td>Houve alteração no pedido no Mercante e não foi comunicada</td>
                            <td><span class="gut-score warning">40</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="table-container">
            <div class="table-header-bar history">
                <span>2. HISTÓRICO ACUMULADO DO CLIENTE (DRILL-DOWN)</span>
                <span style="font-size:10px;color:#a3e635;font-weight:500;">Filtro Ativo: Lanali Laboratorio (16 SACs totais)</span>
            </div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>Data</th>
                            <th>GUT</th>
                            <th>Colaborador</th>
                            <th>Causa / Histórico de Falhas Registradas</th>
                            <th>Produto</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="background:rgba(239, 68, 68, 0.05);">
                            <td style="white-space:nowrap;color:#f87171;">15/04/2026</td>
                            <td><span class="gut-score danger">216</span></td>
                            <td>Mariana C.</td>
                            <td><b style="color:#f8fafc">Atual:</b> Cliente solicitou Ciclohexano e enviamos Ciclohexanona</td>
                            <td>-</td>
                        </tr>
                        <tr>
                            <td style="white-space:nowrap;color:#64748b;">21/03/2025</td>
                            <td><span class="gut-score" style="background:#334155;">72</span></td>
                            <td>Vitor C.</td>
                            <td>Pedido do cliente saiu sem valor acordado. Frasco/rótulo em branco</td>
                            <td>Ácido Acético</td>
                        </tr>
                        <tr>
                            <td style="white-space:nowrap;color:#64748b;">05/12/2024</td>
                            <td><span class="gut-score" style="background:#334155;">72</span></td>
                            <td>Não Ident.</td>
                            <td>Cliente está com dificuldade para abrir as tampas dos frascos</td>
                            <td>-</td>
                        </tr>
                        <tr>
                            <td style="white-space:nowrap;color:#64748b;">10/04/2023</td>
                            <td><span class="gut-score" style="background:#334155;">72</span></td>
                            <td>Sistema</td>
                            <td>Produto absorveu umidade, frasco inadequado para transporte</td>
                            <td>-</td>
                        </tr>
                        <tr>
                            <td style="white-space:nowrap;color:#64748b;">23/08/2022</td>
                            <td><span class="gut-score" style="background:#334155;">72</span></td>
                            <td>Equipe Lab</td>
                            <td>Produto entregue com avaria externa na caixa principal</td>
                            <td>-</td>
                        </tr>
                        <tr>
                            <td style="white-space:nowrap;color:#64748b;">27/05/2022</td>
                            <td><span class="gut-score" style="background:#334155;">90</span></td>
                            <td>Logística</td>
                            <td>Produto foi enviado ao cliente com o frasco sem rótulo legal</td>
                            <td>Hexano PA</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

    </div>
</div>

</body>
</html>
