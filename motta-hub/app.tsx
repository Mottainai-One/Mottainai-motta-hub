import { createContext, useCallback, useContext, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { createRoot } from 'react-dom/client';

type CatalogTable = { id: string; fullName: string; description: string };
type TableDetail = CatalogTable & { columns: { name: string; description: string }[] };
type Resource<T> =
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; code?: number; message?: string };
type User = { id: string; email: string; role: 'DBA' | 'FULLSTACK' | 'USER' };
type Session = { user: null } | { user: User; csrfToken: string };
type Auth = { user: User; csrfToken: string; refresh: () => void; logout: () => Promise<void>; loggingOut: boolean; error: string };
const AuthContext = createContext<Auth | null>(null);
const roleLabels = { DBA: 'DBA', FULLSTACK: 'FullStack', USER: 'Usuário' };

async function responseError(response: Response, fallback: string) {
  try {
    const body = await response.json() as { error?: unknown };
    return typeof body.error === 'string' && body.error ? body.error : fallback;
  } catch { return fallback; }
}

function AuthGate({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Resource<Session>>({ status: 'loading' });
  const [loggingOut, setLoggingOut] = useState(false);
  const [error, setError] = useState('');
  const request = useRef(0);
  const refresh = useCallback(() => {
    const current = ++request.current;
    setSession({ status: 'loading' });
    setError('');
    void (async () => {
      try {
        const response = await fetch('/api/session', { credentials: 'same-origin', cache: 'no-store' });
        if (!response.ok) {
          const message = await responseError(response, 'Não foi possível verificar sua sessão.');
          if (current === request.current) setSession({ status: 'error', message });
          return;
        }
        const data = await response.json() as Session;
        if (current === request.current) setSession({ status: 'success', data });
      } catch {
        if (current === request.current) setSession({ status: 'error', message: 'Não foi possível verificar sua sessão.' });
      }
    })();
  }, []);
  useEffect(() => { refresh(); return () => { request.current += 1; }; }, [refresh]);
  async function logout() {
    if (session.status !== 'success' || !session.data.user || loggingOut) return;
    setLoggingOut(true);
    setError('');
    try {
      const response = await fetch('/api/logout', {
        method: 'POST', credentials: 'same-origin', headers: { 'X-CSRF-Token': session.data.csrfToken },
      });
      if (response.status === 401) { refresh(); return; }
      if (!response.ok) { setError(await responseError(response, 'Não foi possível sair. Tente novamente.')); return; }
      request.current += 1;
      setSession({ status: 'success', data: { user: null } });
      window.location.hash = '#/tabelas';
    } catch { setError('Não foi possível sair. Tente novamente.'); }
    finally { setLoggingOut(false); }
  }
  if (session.status === 'loading') return <div className="auth-layout"><p role="status">Verificando sessão…</p></div>;
  if (session.status === 'error') return <div className="auth-layout"><ErrorState retry={refresh} message={session.message} /></div>;
  if (!session.data.user) return <Login onLogin={data => { request.current += 1; setSession({ status: 'success', data }); }} />;
  return <AuthContext.Provider value={{ user: session.data.user, csrfToken: session.data.csrfToken, refresh, logout, loggingOut, error }}>{children}</AuthContext.Provider>;
}

function Login({ onLogin }: { onLogin: (session: Session) => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  useEffect(() => { document.title = 'Entrar · Motta-hub'; }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError('');
    try {
      const response = await fetch('/api/login', {
        method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      setPassword('');
      if (!response.ok) { setError(await responseError(response, 'Não foi possível entrar. Verifique suas credenciais.')); return; }
      const data = await response.json() as Session;
      if (!data.user) { setError('Não foi possível entrar. Verifique suas credenciais.'); return; }
      onLogin(data);
    } catch { setError('Não foi possível entrar. Tente novamente.'); }
    finally { setPassword(''); setPending(false); }
  }
  return <main className="auth-split">
    <section className="auth-card" aria-labelledby="login-title">
      <span className="auth-logo" aria-hidden="true">P<span /></span>
      <h1 id="login-title">Entrar no catálogo</h1><p className="form-intro">Use sua conta para consultar as tabelas cadastradas.</p>
      <form className="catalog-form" onSubmit={submit} aria-busy={pending}>
        <div className="form-field"><label htmlFor="login-email">E-mail</label><input id="login-email" name="email" type="email" autoComplete="username" required value={email} onChange={event => setEmail(event.target.value)} disabled={pending} /></div>
        <div className="form-field"><label htmlFor="login-password">Senha</label><input id="login-password" name="password" type="password" autoComplete="current-password" required value={password} onChange={event => setPassword(event.target.value)} disabled={pending} /></div>
        {error ? <p className="form-error" role="alert">{error}</p> : null}
        <button className="btn" type="submit" disabled={pending}>{pending ? 'Entrando…' : 'Entrar'}</button>
      </form>
    </section>
    <aside className="auth-brand-panel" aria-hidden="true">
      <div className="auth-brand-art"><span className="auth-brand-mark">P<span /></span><strong>Motta-hub</strong><p>Catálogo de tabelas e colunas</p></div>
    </aside>
  </main>;
}

function subscribeToRoute(onChange: () => void) {
  window.addEventListener('hashchange', onChange);
  return () => window.removeEventListener('hashchange', onChange);
}
const readHash = () => window.location.hash;

function searchURL(term: string) {
  return '#/tabelas' + (term ? `?${new URLSearchParams({ name: term })}` : '');
}

function useResource<T>(url: string, delay = 0) {
  const refresh = useContext(AuthContext)!.refresh;
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<{ url: string; attempt: number; value: Resource<T> }>();
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(url, { signal: controller.signal, credentials: 'same-origin', cache: 'no-store' });
        if (controller.signal.aborted) return;
        if (response.status === 401) { refresh(); return; }
        if (!response.ok) {
          const message = await responseError(response, 'Não foi possível carregar os dados.');
          if (!controller.signal.aborted) {
            setResult({ url, attempt, value: { status: 'error', code: response.status, message } });
          }
          return;
        }
        const data = await response.json() as T;
        if (!controller.signal.aborted) setResult({ url, attempt, value: { status: 'success', data } });
      } catch {
        if (!controller.signal.aborted) setResult({ url, attempt, value: { status: 'error' } });
      }
    }
    const timer = window.setTimeout(() => { void load(); }, delay);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [url, attempt, delay, refresh]);
  const resource: Resource<T> = result?.url === url && result.attempt === attempt
    ? result.value : { status: 'loading' };
  return { resource, retry: () => setAttempt(value => value + 1) };
}

type SearchHandler = (term: string, live?: boolean) => void;

function SearchForm({ term, global = false, onSearch, documentation = false }: {
  term: string; global?: boolean; onSearch: SearchHandler; documentation?: boolean;
}) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSearch(term.trim());
  }
  if (global) return (
    <form id="global-form" className="global-search" role="search" onSubmit={submit}>
      <svg className="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></svg>
      <input id="global-search" type="search" aria-label={documentation ? 'Buscar documentações no Motta-hub' : 'Buscar tabelas no Motta-hub'} placeholder={documentation ? 'Busque por documentações.' : 'Busque por tabelas.'} autoComplete="off" value={term} onChange={event => onSearch(event.target.value, true)} />
    </form>
  );
  return (
    <form id="search-form" className="search-form" role="search" onSubmit={submit}>
      <div className="search-field">
        <label htmlFor="table-search">Nome da Tabela</label>
        <input id="table-search" type="search" aria-label="Nome da tabela ou schema" placeholder="Buscar tabela" autoComplete="off" value={term} onChange={event => onSearch(event.target.value, true)} />
      </div>
      <button className="btn secondary" type="submit">Pesquisar</button>
      {term ? <button className="btn tertiary" id="clear-search" type="button" onClick={() => onSearch('', true)}>Limpar pesquisa</button> : null}
    </form>
  );
}

function Shell({ children, term, onSearch, hash }: {
  children: ReactNode; term: string; onSearch: SearchHandler; hash: string;
}) {
  const auth = useContext(AuthContext)!;
  const main = useRef<HTMLElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const previousHash = useRef(hash);
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => {
    if (previousHash.current !== hash) {
      window.scrollTo(0, 0);
      setMenuOpen(false);
      if (!(document.activeElement instanceof HTMLInputElement)) main.current?.focus();
      previousHash.current = hash;
    }
  }, [hash]);
  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') { setMenuOpen(false); menuButton.current?.focus(); } };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', onKey); document.body.style.overflow = ''; };
  }, [menuOpen]);
  const logoutLabel = auth.loggingOut ? 'Saindo…' : 'Sair';
  return <>
    <a className="skip-link" href="#main" onClick={event => { event.preventDefault(); main.current?.focus(); }}>Ir para o conteúdo</a>
    <button ref={menuButton} type="button" className={`menu-toggle${menuOpen ? ' open' : ''}`} aria-label={menuOpen ? 'Fechar menu de navegação' : 'Abrir menu de navegação'} aria-expanded={menuOpen} aria-controls="sidebar" onClick={() => setMenuOpen(open => !open)}>
      <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">{menuOpen ? <path d="M6 6l12 12M18 6 6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}</svg>
    </button>
    {menuOpen ? <button type="button" className="sidebar-overlay" aria-label="Fechar menu de navegação" onClick={() => { setMenuOpen(false); menuButton.current?.focus(); }} /> : null}
    <nav id="sidebar" className={`sidebar${menuOpen ? ' open' : ''}`} aria-label="Navegação principal">
      <a className="brand" href="#/inicio" aria-label="Motta-hub, início"><span className="brand-mark" aria-hidden="true">M<span /></span><strong>Motta-hub</strong></a>
      <p id="group-pages" className="sidebar-group-title">Páginas</p>
      <ul className="sidebar-group" aria-labelledby="group-pages">
        <li><a className="nav-item" href="#/inicio" aria-current={['/', '/inicio'].includes(hash) ? 'page' : undefined}><svg className="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m3 11 9-8 9 8M5 9v12h14V9M9 21v-8h6v8" /></svg><span>Início</span></a></li>
        <li><a className="nav-item" href="#/tabelas" aria-current={hash.startsWith('/tabelas') ? 'page' : undefined}><svg className="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 10h18M3 15h18M10 10v10" /></svg><span>Tabelas</span></a></li>
        {auth.user.role !== 'USER' ? <li><a className="nav-item" href="#/solicitacoes" aria-current={hash.startsWith('/solicitacoes') ? 'page' : undefined}><svg className="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0" /></svg><span>Solicitações</span></a></li> : null}
        <li><a className="nav-item" href="#/documentacoes" aria-current={hash === '/documentacoes' ? 'page' : undefined}><svg className="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l4 4v14H6zM15 3v5h4M9 12h7M9 16h7" /></svg><span>Documentações</span></a></li>
      </ul>
      <footer className="sidebar-footer">
        <span className="sidebar-account" title={auth.user.email}><svg className="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" /></svg>{roleLabels[auth.user.role]}</span>
        <button className="sidebar-logout" type="button" aria-label={logoutLabel} disabled={auth.loggingOut} onClick={() => { void auth.logout(); }}>
          <svg className="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 8l-4 4 4 4M6 12h10" /></svg>
          <span className="tooltip" aria-hidden="true">{logoutLabel}</span>
        </button>
      </footer>
    </nav>
    <div className="content-shell">
      <header className="topbar">
        <SearchForm term={term} global onSearch={onSearch} documentation={hash === '/documentacoes'} />
        <div className="session-controls">
          <NotificationCenter />
          <span className="session-user">Você está logado como: <strong title={auth.user.email}>{auth.user.email}</strong></span>
          <span className="session-divider" aria-hidden="true">|</span>
          <span className="session-role">Perfil: <strong>{roleLabels[auth.user.role]}</strong></span>
        </div>
      </header>
      <main id="main" tabIndex={-1} ref={main}>{auth.error ? <p className="form-error" role="alert">{auth.error}</p> : null}{children}</main>
    </div>
  </>;
}

function ErrorState({ retry, message }: { retry: () => void; message?: string }) {
  return <div className="empty-state" role="alert">
    <h2>Não foi possível carregar os dados</h2>
    <p>{message || 'Verifique se o backend está em execução e tente novamente.'}</p>
    <button className="btn secondary" type="button" id="retry" onClick={retry}>Tentar novamente</button>
  </div>;
}

type Overview = { tableCount: number; columnCount: number; documentedColumnCount: number; schemas: { name: string; tableCount: number }[]; source: string };
const fold = (value: string) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

function Home() {
  const auth = useContext(AuthContext)!;
  const overview = useResource<Overview>('/api/overview');
  const catalog = useResource<{ tables: CatalogTable[] }>('/api/tables');
  const [query, setQuery] = useState('');
  const [schema, setSchema] = useState('');
  const [sort, setSort] = useState('name');
  const [onlyFavorites, setOnlyFavorites] = useState(false);
  const [layout, setLayout] = useState<'cards' | 'list'>('cards');
  const [limit, setLimit] = useState(9);
  const [favorites, setFavorites] = useState<string[]>([]);
  const favoriteKey = `motta-favorites:${auth.user.id}`;
  useEffect(() => {
    document.title = 'Início · Motta-hub';
    try { const saved: unknown = JSON.parse(localStorage.getItem(favoriteKey) || '[]'); setFavorites(Array.isArray(saved) ? saved.filter((item): item is string => typeof item === 'string') : []); }
    catch { setFavorites([]); }
  }, [favoriteKey]);
  useEffect(() => { setLimit(9); }, [query, schema, onlyFavorites, sort]);
  function favorite(id: string) {
    const next = favorites.includes(id) ? favorites.filter(value => value !== id) : [...favorites, id];
    setFavorites(next);
    try { localStorage.setItem(favoriteKey, JSON.stringify(next)); } catch { /* Favoritos continuam disponíveis nesta visita. */ }
  }
  function reset() { setQuery(''); setSchema(''); setOnlyFavorites(false); setSort('name'); }
  const tables = catalog.resource.status === 'success' ? catalog.resource.data.tables : [];
  const filtered = tables.filter(table => (!schema || table.fullName.split('.')[0] === schema)
    && (!onlyFavorites || favorites.includes(table.id))
    && fold(`${table.fullName} ${table.description}`).includes(fold(query.trim())))
    .sort((a, b) => sort === 'reverse' ? b.fullName.localeCompare(a.fullName) : a.fullName.localeCompare(b.fullName));
  const data = overview.resource.status === 'success' ? overview.resource.data : null;
  const coverage = data?.columnCount ? Math.round(data.documentedColumnCount / data.columnCount * 100) : 0;
  return <div className="hub-home">
    <section className="hub-hero" aria-labelledby="home-title">
      <div><p className="hub-eyebrow">MOTTAINAI / CENTRAL DE CONHECIMENTO</p><h1 id="home-title" tabIndex={-1}>Menos procura.<br /><em>Mais contexto.</em></h1>
        <p>O Motta-hub reúne a documentação operacional e analítica em um só lugar. Descubra tabelas, entenda suas colunas e encontre o contexto dos dados antes de usá-los.</p>
        <div className="hub-actions"><a className="btn" href="#explorar" onClick={event => { event.preventDefault(); document.getElementById('hub-query')?.focus(); document.getElementById('explorar')?.scrollIntoView({ behavior: 'smooth' }); }}>Explorar os dados <span aria-hidden="true">↗</span></a><a className="hub-text-link" href="#guia" onClick={event => { event.preventDefault(); document.getElementById('guia')?.scrollIntoView({ behavior: 'smooth' }); }}>Como funciona ↓</a></div>
      </div>
      <aside className="hub-map" aria-label="Organização do catálogo"><span className="hub-map-tag">UM PONTO DE PARTIDA</span><strong>Motta-hub</strong><div className="hub-map-line" /><div className="hub-map-nodes"><span>Schema</span><span>Tabela</span><span>Coluna</span></div><p>Da visão geral ao detalhe.<br />Documentação, não execução de dados.</p></aside>
    </section>
    <section className="hub-metrics" aria-label="Visão geral do catálogo" aria-busy={overview.resource.status === 'loading'}>
      {overview.resource.status === 'error' ? <ErrorState retry={overview.retry} message={overview.resource.message} /> : <>
        <button type="button" onClick={() => { reset(); document.getElementById('explorar')?.scrollIntoView({ behavior: 'smooth' }); }}><span>Tabelas no catálogo</span><strong>{data ? data.tableCount.toLocaleString('pt-BR') : '…'}</strong><small>Explore o inventário ↗</small></button>
        <button type="button" onClick={() => document.getElementById('schemas')?.scrollIntoView({ behavior: 'smooth' })}><span>Schemas disponíveis</span><strong>{data ? data.schemas.length : '…'}</strong><small>Navegue por domínio ↗</small></button>
        <div><span>Colunas cadastradas</span><strong>{data ? data.columnCount.toLocaleString('pt-BR') : '…'}</strong><small>Estrutura e significado</small></div>
        <div><span>Colunas com metadados</span><strong>{data ? `${coverage}%` : '…'}</strong><small>{data ? `${data.documentedColumnCount.toLocaleString('pt-BR')} de ${data.columnCount.toLocaleString('pt-BR')} colunas` : 'Carregando cobertura'}</small><progress value={coverage} max={100} aria-label="Colunas com informações cadastradas" /></div>
      </>}
    </section>
    <section id="schemas" className="hub-section"><div className="hub-section-title"><div><p className="hub-eyebrow">01 / MAPA DO CATÁLOGO</p><h2>Escolha por onde começar</h2></div><button type="button" className="btn tertiary" onClick={overview.retry}>Atualizar indicadores</button></div>
      <div className="hub-schema-grid">{data?.schemas.map(item => <button type="button" key={item.name} aria-pressed={schema === item.name} onClick={() => { setSchema(current => current === item.name ? '' : item.name); document.getElementById('explorar')?.scrollIntoView({ behavior: 'smooth' }); }}><span>SCHEMA</span><strong>{item.name}</strong><small>{item.tableCount} tabelas <span aria-hidden="true">↗</span></small><meter min={0} max={Math.max(1, data.tableCount)} value={item.tableCount} aria-label={`${item.name}: ${item.tableCount} tabelas`} /></button>)}</div>
    </section>
    <section id="explorar" className="hub-section"><div className="hub-section-title"><div><p className="hub-eyebrow">02 / EXPLORAÇÃO</p><h2>Encontre seu próximo dado</h2></div>{auth.user.role === 'DBA' ? <a className="btn secondary" href="#/nova-tabela">Cadastrar tabela +</a> : null}</div>
      <div className="hub-filters"><div className="search-field"><label htmlFor="hub-query">Busca por tabela ou descrição</label><input id="hub-query" type="search" placeholder="Digite um nome, assunto ou palavra-chave…" value={query} onChange={event => setQuery(event.target.value)} maxLength={256} /></div>
        <div><label htmlFor="hub-schema">Schema</label><select id="hub-schema" value={schema} onChange={event => setSchema(event.target.value)}><option value="">Todos os schemas</option>{data?.schemas.map(item => <option key={item.name}>{item.name}</option>)}</select></div>
        <div><label htmlFor="hub-sort">Ordenação</label><select id="hub-sort" value={sort} onChange={event => setSort(event.target.value)}><option value="name">Nome: A → Z</option><option value="reverse">Nome: Z → A</option></select></div>
      </div>
      <div className="hub-result-tools"><div className="hub-actions"><button className="hub-chip" type="button" aria-pressed={onlyFavorites} onClick={() => setOnlyFavorites(value => !value)}>Favoritos ({favorites.length})</button><button className="btn tertiary" type="button" onClick={reset}>Limpar filtros</button></div><div className="view-toggle" role="group" aria-label="Layout dos resultados"><button type="button" aria-pressed={layout === 'cards'} onClick={() => setLayout('cards')}>Cards</button><button type="button" aria-pressed={layout === 'list'} onClick={() => setLayout('list')}>Lista</button></div></div>
      <div aria-live="polite" aria-busy={catalog.resource.status === 'loading'}>{catalog.resource.status === 'loading' ? <p role="status">Carregando catálogo…</p> : catalog.resource.status === 'error' ? <ErrorState retry={catalog.retry} message={catalog.resource.message} /> : <><p className="result-count">{filtered.length} tabelas encontradas · exibindo {Math.min(limit, filtered.length)}</p>
        {filtered.length ? <div className={`hub-table-grid ${layout}`}>{filtered.slice(0, limit).map(table => <article className="hub-table" key={table.id}><div className="hub-table-top"><span>{table.fullName.split('.')[0]}</span><button type="button" aria-label={`${favorites.includes(table.id) ? 'Remover dos' : 'Adicionar aos'} favoritos: ${table.fullName}`} aria-pressed={favorites.includes(table.id)} onClick={() => favorite(table.id)}>{favorites.includes(table.id) ? '★' : '☆'}</button></div><a href={`#/tabelas/${encodeURIComponent(table.id)}`}><h3>{table.fullName.split('.').slice(1).join('.')}</h3><p>{table.description || 'Descrição ainda não cadastrada.'}</p><span className="hub-table-open">Ver colunas e detalhes <span aria-hidden="true">↗</span></span></a></article>)}</div> : <div className="empty-state"><h3>Nenhuma tabela com esses filtros</h3><p>{onlyFavorites ? 'Favorite tabelas para encontrá-las aqui ou remova os filtros.' : 'Tente outro termo ou escolha todos os schemas.'}</p><button type="button" className="btn secondary" onClick={reset}>Ver todas as tabelas</button></div>}
        {filtered.length > limit ? <button className="btn secondary hub-more" type="button" onClick={() => setLimit(value => value + 9)}>Mostrar mais 9 tabelas</button> : null}</>}
      </div>
    </section>
    <section id="guia" className="hub-guide"><div><p className="hub-eyebrow">03 / DO CONTEXTO À CONSULTA</p><h2>Conheça antes<br />de consultar.</h2><p>O hub é um catálogo de metadados: nomes, descrições e estrutura. Não contém resultados de consultas nem executa SQL.</p><a className="hub-text-link" href="#/tabelas">Abrir catálogo completo ↗</a></div><div className="hub-steps"><details open><summary>01. Descubra a tabela</summary><p>Use a busca ou escolha um schema. A descrição ajuda a entender a finalidade da tabela. O catálogo foi iniciado com a planilha Mottainai importada e pode receber atualizações locais autorizadas.</p></details><details><summary>02. Entenda as colunas</summary><p>Abra os detalhes para consultar os campos e as descrições cadastradas. Descrição ausente é uma lacuna de documentação, não um dado inexistente.</p></details><details><summary>03. Use o SQL com cuidado</summary><p>A planilha não fornece o DDL oficial. O DBA pode cadastrar scripts ALTER TABLE para a tabela aberta. O servidor verifica comandos e tabela alvo, mas não valida o dialeto completo. O Motta-hub não executa SQL nem altera colunas automaticamente pelo script.</p></details><details><summary>04. Organize e contribua</summary><p>Marque favoritos para esta conta neste navegador. Somente DBA pode cadastrar tabelas e adicionar ou remover colunas diretamente. FullStack pode solicitar colunas em tabelas existentes e cancelar solicitações abertas; o perfil Usuário tem acesso de consulta.</p></details><details><summary>O que significa a cobertura de metadados?</summary><p>A cobertura considera colunas com alguma informação cadastrada, como descrição, tipagem, obrigatoriedade ou observações. Não significa documentação de negócio completa nem validação do schema físico. Na planilha importada, 872 dos 883 campos não têm descrição de propriedade explícita, e 39 tabelas não têm campos detalhados. Essas lacunas foram preservadas, sem inventar informações.</p></details><details><summary>De onde vêm os dados?</summary><p>{data?.source || 'Consulte a origem após o carregamento dos indicadores.'} Os indicadores acima refletem o catálogo local completo, com as tabelas e os campos da planilha importada e eventuais alterações locais autorizadas, sem dados de demonstração. São contagens de metadados, não volume de registros de negócio.</p></details></div></section>
    <footer className="hub-footer"><strong>Motta-hub</strong><span>Documentação conectada. Conhecimento compartilhado.</span><button type="button" className="btn tertiary" onClick={() => { window.scrollTo({ top: 0, behavior: 'smooth' }); document.getElementById('home-title')?.focus(); }}>Voltar ao topo ↑</button></footer>
  </div>;
}

function Catalog({ term, onSearch }: { term: string; onSearch: SearchHandler }) {
  const canCreate = useContext(AuthContext)!.user.role === 'DBA';
  const { resource, retry } = useResource<{ tables: CatalogTable[] }>(`/api/tables?${new URLSearchParams({ q: term.trim() })}`, 250);
  useEffect(() => { document.title = 'Tabelas · Motta-hub'; }, []);
  return <>
    <nav className="breadcrumbs" aria-label="Caminho de navegação"><span>Motta-hub</span><span className="separator" aria-hidden="true">›</span><span aria-current="page">Tabelas</span></nav>
    <div className="heading-actions"><div className="page-heading"><h1>Tabelas</h1><p>Navegue pelas tabelas para descobrir e acessar conteúdos.</p></div>{canCreate ? <a className="btn" href={`#/nova-tabela?${new URLSearchParams({ name: term })}`}>Nova tabela</a> : null}</div>
    <SearchForm term={term} onSearch={onSearch} />
    <section id="results" aria-live="polite" aria-label="Resultados da pesquisa" aria-busy={resource.status === 'loading'}>
      {resource.status === 'loading' ? <p className="result-count">Carregando tabelas…</p> :
        resource.status === 'error' ? <ErrorState retry={retry} message={resource.message} /> :
          resource.data.tables.length ? <>
            <p className="result-count">{resource.data.tables.length} {resource.data.tables.length === 1 ? 'tabela encontrada' : 'tabelas encontradas'}</p>
            <div className="results">{resource.data.tables.map(table =>
              <article className="table-card" key={table.id}>
                <a className="table-link" href={`#/tabelas/${encodeURIComponent(table.id)}?${new URLSearchParams({ name: term })}`}>{table.fullName}</a>
                <p className="card-description">{table.description}</p>
              </article>
            )}</div>
          </> : <div className="empty-state"><h2>Nenhuma tabela encontrada</h2><p>Tente outro nome de tabela ou schema.</p></div>}
    </section>
  </>;
}

type Documentation = { id: string; schema: string; title: string; content: string; sourcePath?: string; sourceUrl?: string; filename?: string; format?: string };
type DocumentationCatalog = { schemas: string[]; documents: Documentation[] };

function documentationRoute(doc: Documentation, term: string, anchor = '') {
  const parameters = new URLSearchParams({ schema: doc.schema, document: doc.id });
  if (term) parameters.set('name', term);
  if (anchor) parameters.set('anchor', anchor);
  return `#/documentacoes?${parameters}`;
}

const documentationPrefix = (id: string) => `doc-${encodeURIComponent(id).replace(/-/g, '%2D')}-`;
const headingSlug = (text: string) => text.toLowerCase().replace(/[^\p{L}\p{N}_\s-]/gu, '').trim().replace(/\s+/g, '-') || 'section';
function decodedAnchor(anchor: string) {
  try { return decodeURIComponent(anchor); } catch { return anchor; }
}
function scrollDocumentation(doc: Documentation, anchor: string) {
  const prefix = documentationPrefix(doc.id);
  const value = decodedAnchor(anchor);
  const target = anchor ? document.getElementById(prefix + value) ?? document.getElementById(prefix + headingSlug(value)) : document.getElementById(`documentation-${encodeURIComponent(doc.id)}`);
  target?.scrollIntoView({ block: 'start' });
  target?.focus({ preventScroll: true });
}

function documentationAsset(raw: string, doc?: Documentation): URL | null {
  try {
    const root = new URL('/documentation-files/', window.location.origin);
    const source = doc?.sourceUrl ? new URL(doc.sourceUrl, root) : doc?.sourcePath ? new URL(doc.sourcePath.split('/').map(encodeURIComponent).join('/'), root) : root;
    const base = source.origin === root.origin && source.pathname.startsWith(root.pathname) ? source : root;
    const url = new URL(raw, base);
    const path = decodeURIComponent(url.pathname);
    if (url.origin !== root.origin || !url.pathname.startsWith(root.pathname) || !path.startsWith(root.pathname)
      || path.split('/').some(part => part === '..' || part === '.') || /[\\\u0000-\u001f]/.test(path) || url.username || url.password) return null;
    return url;
  } catch { return null; }
}

function registeredDocumentation(url: URL, documents: Documentation[]) {
  const sources = documents.flatMap(item => {
    const source = item.sourceUrl || item.sourcePath ? documentationAsset(item.sourceUrl ?? '', item) : null;
    return source ? [{ item, source }] : [];
  });
  const exact = sources.filter(entry => entry.source.pathname === url.pathname);
  if (exact.length === 1) return exact[0];
  if (exact.length > 1) return null;
  const matches = sources.filter(entry => decodedAnchor(entry.source.pathname).toLowerCase() === decodedAnchor(url.pathname).toLowerCase());
  return matches.length === 1 ? matches[0] : null;
}

function documentationLink(raw: string, doc: Documentation, documents: Documentation[], term: string) {
  const value = raw.trim();
  if (!value || /[\u0000-\u001f\u007f]/.test(value) || value.includes('\\')) return null;
  if (value.startsWith('#')) return documentationRoute(doc, term, decodedAnchor(value.slice(1)));
  if (!documentationAsset(value, doc) && (/^[a-z][a-z\d+.-]*:/i.test(value) || value.startsWith('//'))) {
    try {
      const url = new URL(value, window.location.origin);
      if (!['http:', 'https:', 'mailto:'].includes(url.protocol) || url.username || url.password) return null;
      return url.href;
    } catch { return null; }
  }
  const url = documentationAsset(value, doc);
  if (!url) return null;
  const registered = registeredDocumentation(url, documents);
  if (!registered) return null;
  if (/\.(md|markdown)$/i.test(registered.source.pathname)) return documentationRoute(registered.item, term, decodedAnchor(url.hash.slice(1)));
  registered.source.search = url.search;
  registered.source.hash = url.hash;
  return registered.source.href;
}

function DocumentationContent({ doc, documents, term, onOpen }: { doc: Documentation; documents: Documentation[]; term: string; onOpen: (doc: Documentation, anchor: string) => void }) {
  const { content, format } = doc;
  if (!content.trim()) return <p>Este arquivo não possui conteúdo textual. Consulte o arquivo original abaixo.</p>;
  const filename = (doc.filename || doc.sourcePath || doc.sourceUrl || '').split(/[?#]/)[0];
  if (!/^(md|markdown)$/i.test(format ?? '') && !/\.(md|markdown)$/i.test(filename)) return <pre className="documentation-plain"><code>{content}</code></pre>;
  const usedIds = new Set<string>();
  let key = 0;
  const references = new Map<string, { url: string; title?: string }>();
  const referenceKey = (value: string) => value.trim().replace(/\s+/g, ' ').toLowerCase();
  const lines = content.replace(/\r\n?/g, '\n').split('\n');
  // Reference definitions are collected outside fenced code, never interpreted as HTML.
  let fence = '';
  for (let i = 0; i < lines.length; i++) {
    const marker = /^ {0,3}(`{3,}|~{3,})/.exec(lines[i]);
    if (marker) {
      if (!fence) fence = marker[1];
      else if (marker[1][0] === fence[0] && marker[1].length >= fence.length && /^ {0,3}(`+|~+)\s*$/.test(lines[i])) fence = '';
      continue;
    }
    if (fence) continue;
    const definition = /^ {0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))(?:\s+["'](.*)["'])?\s*$/.exec(lines[i]);
    if (definition) { references.set(referenceKey(definition[1]), { url: definition[2] ?? definition[3], title: definition[4] }); lines[i] = ''; }
  }
  function inline(text: string, depth = 0, inLink = false): { nodes: ReactNode[]; plain: string } {
    if (depth > 32) return { nodes: [text], plain: text };
    const nodes: ReactNode[] = [];
    let plain = '', buffer = '';
    const flush = () => { if (buffer) { nodes.push(buffer); plain += buffer; buffer = ''; } };
    for (let i = 0; i < text.length;) {
      if (text[i] === '\\' && /[\\`*{}_\[\]()#+.!>~|\-]/.test(text[i + 1] ?? '')) { buffer += text[i + 1]; i += 2; continue; }
      if (text[i] === '\n' && / {2}$/.test(buffer)) { buffer = buffer.replace(/ {2}$/, ''); flush(); nodes.push(<br key={key++} />); plain += '\n'; i++; continue; }
      if (text[i] === '`') {
        const run = /^`+/.exec(text.slice(i))![0];
        let end = text.indexOf(run, i + run.length);
        while (end !== -1 && (text[end - 1] === '`' || text[end + run.length] === '`')) end = text.indexOf(run, end + run.length);
        if (end !== -1) {
          flush(); let code = text.slice(i + run.length, end).replace(/\n/g, ' ');
          if (/^ .* $/.test(code) && code.trim()) code = code.slice(1, -1);
          nodes.push(<code key={key++}>{code}</code>); plain += code; i = end + run.length; continue;
        }
      }
      const image = text.startsWith('![', i);
      if ((image || text[i] === '[') && (!inLink || image)) {
        const start = i + (image ? 2 : 1);
        let end = start, nesting = 1;
        for (; end < text.length; end++) {
          if (text[end] === '\\') { end++; continue; }
          if (text[end] === '[') nesting++;
          if (text[end] === ']' && --nesting === 0) break;
        }
        if (end < text.length) {
          let url: string | undefined, title: string | undefined, next = end + 1;
          if (text[next] === '(') {
            let close = next + 1, balance = 1;
            for (; close < text.length; close++) {
              if (text[close] === '\\') { close++; continue; }
              if (text[close] === '(') balance++;
              if (text[close] === ')' && --balance === 0) break;
            }
            if (balance === 0) {
              const destination = /^(?:<([^>]+)>|(\S*?))(?:\s+["'](.*)["'])?$/.exec(text.slice(next + 1, close).trim());
              if (destination) { url = destination[1] ?? destination[2]; title = destination[3]; next = close + 1; }
            }
          } else {
            const ref = /^\[([^\]]*)\]/.exec(text.slice(next));
            const definition = references.get(referenceKey(ref?.[1] || text.slice(start, end)));
            if (definition) { ({ url, title } = definition); if (ref) next += ref[0].length; }
          }
          if (url !== undefined) {
            flush(); const label = inline(text.slice(start, end), depth + 1, true);
            if (image) {
              const asset = documentationAsset(url, doc);
              const local = asset ? registeredDocumentation(asset, documents)?.source : null;
              const href = documentationLink(url, doc, documents, term);
              nodes.push(local ? <img key={key++} src={local.href} alt={label.plain} title={title} loading="lazy" referrerPolicy="no-referrer" /> : <span className="documentation-image-placeholder" key={key++}>{label.plain || 'Imagem'} — imagem não carregada{href && !href.startsWith('#') ? <> (<a href={href} target="_blank" rel="noopener noreferrer" referrerPolicy="no-referrer">abrir imagem</a>)</> : null}</span>);
            } else {
              const href = documentationLink(url, doc, documents, term);
              nodes.push(href ? <a key={key++} href={href} title={title} rel={href.startsWith('#') ? undefined : 'noopener noreferrer'} referrerPolicy="no-referrer" onClick={event => {
                if (href === window.location.hash && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) {
                  event.preventDefault();
                  const parameters = new URLSearchParams(href.split('?')[1]);
                  const target = documents.find(item => item.id === parameters.get('document'));
                  if (target) onOpen(target, parameters.get('anchor') || '');
                }
              }}>{label.nodes}</a> : <span key={key++} title="Endereço não permitido ou arquivo ausente" className="documentation-blocked-link">{label.nodes} — Referência não disponível neste pacote</span>);
            }
            plain += label.plain; i = next; continue;
          }
        }
      }
      const autolink = !inLink ? /^<(https?:\/\/[^<>\s]+|mailto:[^<>\s]+|[^<>\s@]+@[^<>\s@]+\.[^<>\s@]+)>/.exec(text.slice(i)) : null;
      if (autolink) {
        const label = autolink[1], href = documentationLink(label.includes('@') && !/^(https?:|mailto:)/.test(label) ? `mailto:${label}` : label, doc, documents, term);
        if (href) { flush(); nodes.push(<a key={key++} href={href} rel="noopener noreferrer" referrerPolicy="no-referrer">{label}</a>); plain += label; i += autolink[0].length; continue; }
      }
      const delimiter = /^(\*\*\*|___|\*\*|__|~~|\*|_)/.exec(text.slice(i))?.[0];
      if (delimiter && !/\s/.test(text[i + delimiter.length] ?? ' ') && !(delimiter.includes('_') && /[\p{L}\p{N}]/u.test(text[i - 1] ?? ''))) {
        let end = text.indexOf(delimiter, i + delimiter.length);
        while (end !== -1 && (/\s/.test(text[end - 1]) || text[end - 1] === '\\')) end = text.indexOf(delimiter, end + delimiter.length);
        if (end !== -1) {
          flush(); const child = inline(text.slice(i + delimiter.length, end), depth + 1, inLink);
          nodes.push(delimiter === '~~' ? <del key={key++}>{child.nodes}</del> : delimiter.length === 3 ? <em key={key++}><strong>{child.nodes}</strong></em> : delimiter.length === 2 ? <strong key={key++}>{child.nodes}</strong> : <em key={key++}>{child.nodes}</em>);
          plain += child.plain; i = end + delimiter.length; continue;
        }
      }
      buffer += text[i++];
    }
    flush(); return { nodes, plain };
  }
  const listMarker = (line: string) => /^( *)([-+*]|\d+[.)])( +)(.*)$/.exec(line);
  const rule = (line: string) => /^ {0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$/.test(line);
  function cells(line: string) {
    const result: string[] = []; let value = '', codeRun = 0;
    const text = line.trim().replace(/^\|/, '').replace(/(?<!\\)\|$/, '');
    for (let i = 0; i < text.length; i++) {
      if (text[i] === '\\' && text[i + 1] === '|') { value += '|'; i++; continue; }
      if (text[i] === '`') { const run = /^`+/.exec(text.slice(i))![0]; if (!codeRun) codeRun = run.length; else if (run.length === codeRun) codeRun = 0; value += run; i += run.length - 1; continue; }
      if (text[i] === '|' && !codeRun) { result.push(value.trim()); value = ''; } else value += text[i];
    }
    result.push(value.trim()); return result;
  }
  const tableDivider = (line: string) => cells(line).every(cell => /^:?-{3,}:?$/.test(cell));
  function blocks(input: string[], depth = 0): ReactNode[] {
    if (depth > 32) return [<pre key={key++}><code>{input.join('\n')}</code></pre>];
    const result: ReactNode[] = [];
    const startsBlock = (index: number) => /^ {0,3}(#{1,6}(?:\s|$)|`{3,}|~{3,}|>)/.test(input[index]) || !!listMarker(input[index]) || rule(input[index]) || /^ {4}\S/.test(input[index]);
    function heading(level: number, title: string) {
      const rendered = inline(title); const base = headingSlug(rendered.plain);
      let slug = base, suffix = 0; while (usedIds.has(slug)) slug = `${base}-${++suffix}`; usedIds.add(slug);
      const Tag = `h${level}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
      return <Tag key={key++} id={documentationPrefix(doc.id) + slug} tabIndex={-1}>{rendered.nodes}</Tag>;
    }
    for (let i = 0; i < input.length;) {
      if (!input[i].trim()) { i++; continue; }
      const line = input[i], fenced = /^ {0,3}(`{3,}|~{3,})(.*)$/.exec(line);
      if (fenced) {
        const code: string[] = [], indent = /^ */.exec(line)![0].length; i++;
        const closing = new RegExp(`^ {0,3}${fenced[1][0]}{${fenced[1].length},}\\s*$`);
        while (i < input.length && !closing.test(input[i])) code.push(input[i++].replace(new RegExp(`^ {0,${indent}}`), ''));
        if (i < input.length) i++;
        const language = fenced[2].trim().split(/\s/)[0];
        result.push(<pre key={key++}><code data-language={language || undefined}>{code.join('\n')}</code></pre>); continue;
      }
      const atx = /^ {0,3}(#{1,6})(?:\s+(.*)|\s*)$/.exec(line);
      if (atx) { result.push(heading(atx[1].length, (atx[2] ?? '').replace(/\s+#+\s*$/, '').trim())); i++; continue; }
      if (i + 1 < input.length && /^ {0,3}(=+|-+)\s*$/.test(input[i + 1]) && !startsBlock(i)) { result.push(heading(input[i + 1].trim()[0] === '=' ? 1 : 2, line.trim())); i += 2; continue; }
      if (rule(line)) { result.push(<hr key={key++} />); i++; continue; }
      if (/^ {0,3}>/.test(line)) {
        const quote: string[] = []; while (i < input.length && /^ {0,3}>/.test(input[i])) quote.push(input[i++].replace(/^ {0,3}> ?/, ''));
        result.push(<blockquote key={key++}>{blocks(quote, depth + 1)}</blockquote>); continue;
      }
      const marker = listMarker(line);
      if (marker) {
        const indent = marker[1].length, ordered = /^\d/.test(marker[2]), start = ordered ? parseInt(marker[2], 10) : undefined;
        const items: ReactNode[] = [];
        while (i < input.length) {
          const current = listMarker(input[i]);
          if (!current || current[1].length !== indent || /^\d/.test(current[2]) !== ordered || rule(input[i])) break;
          const offset = current[1].length + current[2].length + current[3].length;
          const item = [current[4]]; i++;
          while (i < input.length) {
            if (!input[i].trim()) {
              let next = i + 1; while (next < input.length && !input[next].trim()) next++;
              if (next < input.length && /^ */.exec(input[next])![0].length >= offset) { item.push(''); i++; continue; }
              const sibling = next < input.length ? listMarker(input[next]) : null;
              if (sibling && sibling[1].length === indent) i = next;
              break;
            }
            const spaces = /^ */.exec(input[i])![0].length;
            if (spaces < offset) break;
            item.push(input[i++].slice(offset));
          }
          const task = /^\[([ xX])\]\s+(.*)$/.exec(item[0]);
          if (task) item[0] = task[2];
          items.push(<li key={key++} className={task ? 'documentation-task' : undefined}>{task ? <input type="checkbox" checked={task[1].toLowerCase() === 'x'} disabled aria-label={task[2]} /> : null}{blocks(item, depth + 1)}</li>);
        }
        result.push(ordered ? <ol key={key++} start={start}>{items}</ol> : <ul key={key++}>{items}</ul>); continue;
      }
      if (i + 1 < input.length && line.includes('|') && tableDivider(input[i + 1]) && cells(line).length === cells(input[i + 1]).length) {
        const headers = cells(line), align = cells(input[i + 1]).map(cell => cell.startsWith(':') && cell.endsWith(':') ? 'center' as const : cell.endsWith(':') ? 'right' as const : 'left' as const);
        const rows: string[][] = []; i += 2;
        while (i < input.length && input[i].trim() && input[i].includes('|') && !startsBlock(i)) rows.push(cells(input[i++]));
        result.push(<div className="documentation-table-scroll" tabIndex={0} role="region" aria-label="Tabela da documentação" key={key++}><table><thead><tr>{headers.map((cell, index) => <th key={index} scope="col" style={{ textAlign: align[index] }}>{inline(cell).nodes}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{headers.map((_, column) => <td key={column} style={{ textAlign: align[column] }}>{inline(row[column] ?? '').nodes}</td>)}</tr>)}</tbody></table></div>); continue;
      }
      if (/^ {4}/.test(line)) {
        const code: string[] = []; while (i < input.length && (/^ {4}/.test(input[i]) || !input[i].trim())) code.push(input[i++].slice(4));
        result.push(<pre key={key++}><code>{code.join('\n').trimEnd()}</code></pre>); continue;
      }
      const paragraph = [line]; i++;
      while (i < input.length && input[i].trim() && !startsBlock(i)) {
        if (/^ {0,3}(=+|-+)\s*$/.test(input[i]) || (i + 1 < input.length && input[i].includes('|') && tableDivider(input[i + 1]))) break;
        paragraph.push(input[i++]);
      }
      result.push(<p key={key++}>{inline(paragraph.join('\n')).nodes}</p>);
    }
    return result;
  }
  return <div className="documentation-markdown">{blocks(lines)}</div>;
}

function Documentations({ documents, documentationSchemas, onChanged, onSectionCreated, term, onSearch, schema, onSchemaChange, documentId, anchor }: {
  documents: Documentation[]; documentationSchemas: string[]; onChanged: (documents: Documentation[]) => Promise<void>; onSectionCreated: (name: string) => Promise<void>; term: string; onSearch: SearchHandler;
  schema: string; onSchemaChange: (schema: string) => void; documentId: string; anchor: string;
}) {
  const auth = useContext(AuthContext)!;
  const canManage = auth.user.role === 'DBA';
  const [sectionName, setSectionName] = useState<string | null>(null);
  const [sectionError, setSectionError] = useState('');
  const sectionInput = useRef<HTMLInputElement>(null);
  const sectionButton = useRef<HTMLButtonElement>(null);
  const [draft, setDraft] = useState<{ id: string | null; schema: string; title: string; content: string } | null>(null);
  const [removing, setRemoving] = useState<Documentation | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const titleInput = useRef<HTMLInputElement>(null);
  const newButton = useRef<HTMLButtonElement>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const removeTrigger = useRef<HTMLButtonElement | null>(null);
  const [routeClosed, setRouteClosed] = useState('');
  const routeKey = `${documentId}:${anchor}`;
  const routeOpen = routeClosed !== routeKey;
  useEffect(() => { document.title = 'Documentações · Motta-hub'; }, []);
  useEffect(() => {
    const target = documents.find(item => item.id === documentId);
    if (!target || !routeOpen) return;
    const timer = window.setTimeout(() => scrollDocumentation(target, anchor), 0);
    return () => window.clearTimeout(timer);
  }, [documents, documentId, anchor, routeOpen]);
  useEffect(() => { if (draft) titleInput.current?.focus(); }, [draft?.id]);
  useEffect(() => { if (removing && dialog.current && !dialog.current.open) dialog.current.showModal(); }, [removing]);
  const creatingSection = sectionName !== null;
  useEffect(() => { if (creatingSection) sectionInput.current?.focus(); }, [creatingSection]);
  function closeSectionForm() { setSectionName(null); setSectionError(''); sectionButton.current?.focus(); }
  async function saveSection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    const name = sectionName?.trim() ?? '';
    if (!name || name.length > 128) {
      setSectionError('Informe um nome de seção de 1 a 128 caracteres, sem usar apenas espaços.');
      sectionInput.current?.focus();
      return;
    }
    if (documentationSchemas.some(value => fold(value.trim()) === fold(name))) {
      setSectionError('Já existe uma seção com este nome.');
      sectionInput.current?.focus();
      return;
    }
    setSaving(true); setSectionError('');
    try {
      await onSectionCreated(name);
      setMessage('Seção salva no catálogo do Hub.');
      closeSectionForm();
    } catch (cause) {
      setSectionError(cause instanceof Error ? cause.message : 'Não foi possível salvar a seção.');
    } finally { setSaving(false); }
  }
  function dismissRemoval() {
    if (saving) return;
    dialog.current?.close(); setRemoving(null); removeTrigger.current?.focus();
  }
  function closeForm() { setDraft(null); setError(''); newButton.current?.focus(); }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft || saving) return;
    const title = draft.title.trim(), content = draft.content.trim();
    if (!title || !content) { setError('Preencha o título e o conteúdo sem usar apenas espaços.'); return; }
    const document = { ...documents.find(item => item.id === draft.id), id: draft.id ?? crypto.randomUUID(), schema: draft.schema, title, content };
    const nextDocuments = draft.id ? documents.map(item => item.id === draft.id ? document : item) : [...documents, document];
    setSaving(true); setError('');
    try {
      await onChanged(nextDocuments);
      setMessage(draft.id ? 'Documentação atualizada no catálogo do Hub.' : 'Documentação adicionada ao catálogo do Hub.');
      closeForm();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível salvar a documentação.');
    } finally { setSaving(false); }
  }
  async function removeDocument() {
    if (!removing || saving) return;
    setSaving(true); setError('');
    try {
      await onChanged(documents.filter(item => item.id !== removing.id));
      if (draft?.id === removing.id) setDraft(null);
      setMessage('Documentação removida do catálogo do Hub.');
      dismissRemoval(); newButton.current?.focus();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível excluir a documentação.');
    } finally { setSaving(false); }
  }
  const filtered = documents.filter(item => (!schema || item.schema === schema) && fold(`${item.title} ${item.content}`).includes(fold(term.trim())));
  const selected = documents.find(item => item.id === documentId);
  const visible = selected && !filtered.includes(selected) ? [...filtered, selected] : filtered;
  const groups = [...new Set([...documentationSchemas, ...visible.map(item => item.schema)])];
  return <>
    <nav className="breadcrumbs" aria-label="Caminho de navegação"><span>Motta-hub</span><span className="separator" aria-hidden="true">›</span><span aria-current="page">Documentações</span></nav>
    <div className="heading-actions"><div className="page-heading"><h1>Documentações</h1><p>Navegue pelos conteúdos do Mottainai. Clique em um título para expandir.</p></div>{canManage ? <div className="table-detail-actions"><button ref={sectionButton} className="btn secondary" type="button" aria-expanded={creatingSection} aria-controls="documentation-section-form" onClick={() => { setSectionName(''); setSectionError(''); setMessage(''); }}>Nova seção</button><button ref={newButton} className="btn" type="button" aria-expanded={draft !== null} aria-controls="documentation-form" onClick={() => { setDraft({ id: null, schema: documentationSchemas.find(value => value === schema) ?? documentationSchemas[0] ?? '', title: '', content: '' }); setError(''); setMessage(''); }}>Nova documentação</button></div> : null}</div>
    <p className="documentation-notice">Documentos importados do Mottainai-Hub. Cada pasta de Docs corresponde a uma seção. Alterações feitas por DBA são salvas no catálogo do Hub; os arquivos originais não são modificados.</p>
    <form className="search-form" role="search" onSubmit={event => { event.preventDefault(); onSearch(term.trim()); }}>
      <div className="search-field"><label htmlFor="documentation-schema-filter">Seção</label><select id="documentation-schema-filter" value={schema} onChange={event => onSchemaChange(event.target.value)}><option value="">Todas as seções</option>{documentationSchemas.map(value => <option key={value} value={value}>{value}</option>)}{schema && !documentationSchemas.some(value => value === schema) ? <option value={schema}>Seção desconhecida</option> : null}</select></div>
      <div className="search-field"><label htmlFor="documentation-search">Título ou conteúdo</label><input id="documentation-search" type="search" placeholder="Buscar documentação" maxLength={256} value={term} onChange={event => onSearch(event.target.value, true)} /></div>
      <button className="btn secondary" type="submit">Pesquisar</button>{term ? <button className="btn tertiary" type="button" onClick={() => onSearch('', true)}>Limpar pesquisa</button> : null}
    </form>
    {creatingSection && canManage ? <form id="documentation-section-form" className="catalog-form form-section column-create" aria-labelledby="documentation-section-title" aria-busy={saving} onSubmit={event => { void saveSection(event); }}>
      <h2 className="columns-heading" id="documentation-section-title">Nova seção</h2>
      <div className="form-field"><label htmlFor="documentation-section-name">Nome da seção</label><input ref={sectionInput} id="documentation-section-name" required maxLength={128} disabled={saving} value={sectionName} aria-invalid={!!sectionError} aria-describedby={sectionError ? 'documentation-section-error' : undefined} onChange={event => { setSectionName(event.target.value); setSectionError(''); }} /></div>
      {sectionError ? <p id="documentation-section-error" className="form-error" role="alert">{sectionError}</p> : null}
      <div className="form-actions"><button className="btn" type="submit" disabled={saving}>{saving ? 'Salvando…' : 'Adicionar seção'}</button><button className="btn tertiary" type="button" disabled={saving} onClick={closeSectionForm}>Cancelar</button></div>
    </form> : null}
    {draft && canManage ? <form id="documentation-form" className="catalog-form form-section column-create" aria-busy={saving} onSubmit={event => { void save(event); }}>
      <h2 className="columns-heading">{draft.id ? 'Editar documentação' : 'Nova documentação'}</h2>
      <div className="form-field"><label htmlFor="documentation-schema">Seção</label><select id="documentation-schema" required disabled={saving} value={draft.schema} onChange={event => { const selected = documentationSchemas.find(value => value === event.target.value); if (selected) setDraft({ ...draft, schema: selected }); }}><option value="" disabled>Selecione uma seção</option>{documentationSchemas.map(value => <option key={value} value={value}>{value}</option>)}</select></div>
      <div className="form-field"><label htmlFor="documentation-title">Título</label><input ref={titleInput} id="documentation-title" required maxLength={160} disabled={saving} value={draft.title} onChange={event => setDraft({ ...draft, title: event.target.value })} /></div>
      <div className="form-field"><label htmlFor="documentation-content">Conteúdo</label><textarea id="documentation-content" required rows={8} disabled={saving} value={draft.content} onChange={event => setDraft({ ...draft, content: event.target.value })} /></div>
      {error ? <p className="form-error" role="alert">{error}</p> : null}
      <div className="form-actions"><button className="btn" type="submit" disabled={saving}>{saving ? 'Salvando…' : draft.id ? 'Salvar alterações' : 'Adicionar documentação'}</button><button className="btn tertiary" type="button" disabled={saving} onClick={closeForm}>Cancelar</button></div>
    </form> : null}
    {message ? <p role="status">{message}</p> : null}
    <section aria-label="Documentações do Mottainai">
      <p className="result-count" role="status">{filtered.length} {filtered.length === 1 ? 'documentação encontrada' : 'documentações encontradas'}</p>
      {selected && !filtered.includes(selected) ? <p role="status">Documento aberto pelo link, fora dos filtros atuais. A pesquisa foi preservada.</p> : null}
      {documentId && !selected ? <p role="status">O documento solicitado não foi encontrado.</p> : null}
      {groups.map(group => {
        const items = visible.filter(item => item.schema === group);
        if (!items.length && (schema ? schema !== group : !!term.trim())) return null;
        return <section className="documentation-schema-group" key={group} aria-labelledby={`schema-${encodeURIComponent(group)}`}><h2 className="columns-heading" id={`schema-${encodeURIComponent(group)}`}>{group} <small>({items.length})</small></h2>
      {!items.length ? <p className="result-count">Nenhuma documentação nesta seção</p> : null}
      <div className="column-list">{items.map(item => <article className="column-card documentation-card" key={item.id}>
        <details id={`documentation-${encodeURIComponent(item.id)}`} tabIndex={-1} open={expanded.has(item.id) || (item.id === documentId && routeOpen)} onToggle={event => {
          const open = event.currentTarget.open;
          if (!open && item.id === documentId) setRouteClosed(routeKey);
          setExpanded(previous => { if (previous.has(item.id) === open) return previous; const next = new Set(previous); if (open) next.add(item.id); else next.delete(item.id); return next; });
        }}><summary><span>{item.title}</span><svg className="icon documentation-chevron" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg></summary>{expanded.has(item.id) || (item.id === documentId && routeOpen) ? <div className="documentation-body"><DocumentationContent doc={item} documents={documents} term={term} onOpen={(target, targetAnchor) => {
          setRouteClosed('');
          setExpanded(previous => new Set([...previous, target.id]));
          window.setTimeout(() => scrollDocumentation(target, targetAnchor), 0);
        }} />{item.sourceUrl && documentationAsset(item.sourceUrl, item) ? <footer className="documentation-source"><p>Origem: {item.sourcePath || decodedAnchor(documentationAsset(item.sourceUrl, item)!.pathname.slice('/documentation-files/'.length))}</p><a href={documentationAsset(item.sourceUrl, item)!.href} target="_blank" rel="noopener noreferrer" referrerPolicy="no-referrer">Ver arquivo original{item.format ? ` (${item.format.toUpperCase()})` : ''}</a></footer> : null}</div> : null}</details>
        {canManage ? <div className="documentation-actions"><button className="btn tertiary" type="button" aria-label={`Editar documentação ${item.title}`} onClick={() => { setDraft({ ...item }); setError(''); setMessage(''); }}>Editar</button><button className="column-trash" type="button" aria-label={`Excluir documentação ${item.title}`} onClick={event => { removeTrigger.current = event.currentTarget; setRemoving(item); setError(''); setMessage(''); }}><svg className="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7" /></svg></button></div> : null}
      </article>)}</div></section>;
      })}
      {!visible.length && !groups.some(group => schema ? schema === group : !term.trim()) ? <div className="empty-state"><h2>{documents.length ? 'Nenhuma documentação encontrada' : 'Nenhuma documentação cadastrada'}</h2><p>{documents.length ? 'Tente outra seção, título ou palavra do conteúdo.' : 'Adicione uma seção ou documentação neste catálogo.'}</p></div> : null}
    </section>
    <dialog ref={dialog} className="column-dialog" aria-labelledby="delete-documentation-title" onCancel={event => { event.preventDefault(); dismissRemoval(); }} onClose={() => setRemoving(null)}>
      <h2 id="delete-documentation-title">Excluir documentação?</h2><p>Remover <strong>{removing?.title}</strong> do catálogo do Hub? O arquivo original não será alterado.</p>
      {error ? <p className="form-error" role="alert">{error}</p> : null}
      <div className="form-actions"><button className="btn secondary" type="button" autoFocus disabled={saving} onClick={dismissRemoval}>Cancelar</button><button className="btn danger" type="button" disabled={saving} onClick={() => { void removeDocument(); }}>{saving ? 'Excluindo…' : 'Excluir documentação'}</button></div>
    </dialog>
  </>;
}

function NotFound({ term }: { term: string }) {
  useEffect(() => { document.title = 'Tabela não encontrada'; }, []);
  return <><a className="back-link" href={searchURL(term)}>Voltar para pesquisa</a><div className="empty-state"><h1>Tabela não encontrada</h1><p>Este endereço não corresponde a uma tabela cadastrada.</p></div></>;
}

function Columns({ table, onChanged, creating, onCloseForm }: { table: TableDetail; onChanged: (table: TableDetail) => void; creating: boolean; onCloseForm: () => void }) {
  const auth = useContext(AuthContext)!;
  const canEdit = auth.user.role === 'DBA';
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [removing, setRemoving] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const mounted = useRef(true);
  const busy = useRef(false);
  const nameInput = useRef<HTMLInputElement>(null);
  const removeDialog = useRef<HTMLDialogElement>(null);
  const removeTrigger = useRef<HTMLButtonElement | null>(null);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => { if (creating) nameInput.current?.focus(); }, [creating]);
  useEffect(() => {
    const dialog = removeDialog.current;
    if (removing !== null && dialog && !dialog.open) dialog.showModal();
    if (removing === null && dialog?.open) dialog.close();
  }, [removing]);
  function dismissRemoval() {
    if (busy.current) return;
    setRemoving(null); setError('');
    removeTrigger.current?.focus();
  }
  async function mutate(method: 'POST' | 'DELETE', columnName: string) {
    if (busy.current || !canEdit) return;
    busy.current = true;
    setPending(true); setError(''); setMessage('');
    try {
      const response = await fetch(`/api/tables/${encodeURIComponent(table.id)}/columns`, {
        method, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': auth.csrfToken },
        body: JSON.stringify(method === 'POST' ? { name: columnName.trim(), description } : { name: columnName }),
      });
      if (!mounted.current) return;
      if (response.status === 401) { auth.refresh(); return; }
      if (!response.ok) { setError(await responseError(response, 'Não foi possível alterar as colunas.')); return; }
      const updated = await response.json() as TableDetail;
      if (!mounted.current) return;
      onChanged(updated);
      if (method === 'POST') { setName(''); setDescription(''); onCloseForm(); }
      setRemoving(null);
      setMessage(method === 'POST' ? 'Coluna adicionada ao catálogo.' : 'Coluna removida do catálogo.');
      document.getElementById('new-column')?.focus();
    } catch { if (mounted.current) setError('Falha de conexão. Confira as colunas antes de tentar novamente.'); }
    finally { busy.current = false; if (mounted.current) setPending(false); }
  }
  return <>
    {canEdit && creating ? <form id="new-column-form" className="catalog-form form-section column-create" aria-label="Adicionar coluna" aria-busy={pending} onSubmit={event => { event.preventDefault(); void mutate('POST', name); }}>
      <h2 className="columns-heading">Adicionar coluna</h2><p className="form-intro">Altera apenas a documentação local. Não modifica a planilha nem a tabela no banco de origem.</p>
      <div className="form-field"><label htmlFor="column-name">Nome da coluna</label><input ref={nameInput} id="column-name" required maxLength={128} pattern="[A-Za-z_][A-Za-z0-9_]*" title="Comece com letra ou _; use apenas letras, números e _." value={name} disabled={pending || removing !== null} onChange={event => setName(event.target.value)} /></div>
      <div className="form-field"><label htmlFor="column-description">Descrição (opcional)</label><textarea id="column-description" maxLength={4000} rows={3} value={description} disabled={pending || removing !== null} onChange={event => setDescription(event.target.value)} /></div>
      <div className="form-actions"><button className="btn" type="submit" disabled={pending || removing !== null || table.columns.length >= 200}>{pending ? 'Salvando…' : 'Adicionar coluna'}</button><button className="btn tertiary" type="button" disabled={pending} onClick={() => { onCloseForm(); setError(''); document.getElementById('new-column')?.focus(); }}>Cancelar</button></div>
      {table.columns.length >= 200 ? <p>Limite de 200 colunas atingido.</p> : null}
    </form> : null}
    {error && removing === null ? <p className="form-error" role="alert">{error}</p> : null}
    {message ? <p role="status">{message}</p> : null}
    <div className="column-list" aria-busy={pending}>{table.columns.length ? table.columns.map(column =>
      <article className="column-card column-row" key={column.name}><div className="column-copy"><h3>{column.name}</h3><p>{column.description || 'Sem descrição cadastrada.'}</p></div>
        {canEdit ? <button className="column-trash" type="button" disabled={pending || removing !== null} title={`Excluir coluna ${column.name}`} aria-label={`Excluir coluna ${column.name}`} onClick={event => { removeTrigger.current = event.currentTarget; setRemoving(column.name); setError(''); setMessage(''); }}><svg className="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7" /></svg></button> : null}
      </article>
    ) : <p className="result-count">Nenhuma coluna cadastrada nesta tabela.</p>}</div>
    {canEdit ? <dialog ref={removeDialog} className="column-dialog" aria-labelledby="delete-column-title" aria-describedby="delete-column-description" onCancel={event => { event.preventDefault(); dismissRemoval(); }} onClose={() => { if (!busy.current) setRemoving(null); }}>
      <h2 id="delete-column-title">Excluir coluna?</h2><p id="delete-column-description">Excluir <strong>{removing}</strong> da tabela <strong>{table.fullName}</strong>? Essa ação remove apenas os metadados do catálogo local, não a tabela nem o banco de origem.</p>
      {error ? <p className="form-error" role="alert">{error}</p> : null}
      <div className="form-actions"><button className="btn secondary" type="button" autoFocus disabled={pending} onClick={dismissRemoval}>Cancelar</button><button className="btn danger" type="button" disabled={pending || removing === null} onClick={() => { if (removing !== null) void mutate('DELETE', removing); }}>{pending ? 'Excluindo…' : 'Excluir coluna'}</button></div>
    </dialog> : null}
  </>;
}

type RequestedColumn = { name: string; description: string };
type ColumnRequest = { id: string; tableId: string; tableName: string; reason: string; columns: RequestedColumn[]; author: string; status: 'OPEN' | 'APPROVED' | 'REJECTED' | 'CANCELLED'; revision: number; commented: boolean; createdAt: string; closedAt: string | null; history: { id: number; author: string; action: string; content: string; createdAt: string }[] };
type HubNotification = { id: number; requestId: string; action: string; content: string; createdAt: string; readAt: string | null };
const requestStatusLabels = { OPEN: 'Em processamento', APPROVED: 'Aprovada', REJECTED: 'Recusada', CANCELLED: 'Cancelada' };
const actionLabels: Record<string, string> = { OPEN: 'Abertura', EDIT: 'Revisão das colunas', COMMENT: 'Comentário', APPROVE: 'Aprovação', REJECT: 'Recusa', CANCEL: 'Cancelamento' };
const requestURL = (id: string) => `#/solicitacoes/${encodeURIComponent(id)}`;

async function requestMutation(auth: Auth, url: string, data: unknown) {
  const response = await fetch(url, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': auth.csrfToken }, body: JSON.stringify(data) });
  if (response.status === 401) auth.refresh();
  if (!response.ok) throw new Error(await responseError(response, 'Não foi possível concluir a operação.'));
  const result: unknown = await response.json();
  window.dispatchEvent(new Event('hub-requests-changed'));
  return result;
}

function NotificationCenter() {
  const auth = useContext(AuthContext)!;
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<{ notifications: HubNotification[]; unreadCount: number } | null>(null);
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const region = useRef<HTMLDivElement>(null);
  const refresh = auth.refresh;
  useEffect(() => {
    if (auth.user.role === 'USER') return;
    let disposed = false;
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch('/api/notifications', { signal: controller.signal, credentials: 'same-origin', cache: 'no-store' });
        if (disposed) return;
        if (response.status === 401) { refresh(); return; }
        if (!response.ok) throw new Error(await responseError(response, 'Falha ao carregar notificações.'));
        const result = await response.json() as { notifications: HubNotification[]; unreadCount: number };
        if (!disposed) { setData(result); setError(''); }
      } catch { if (!disposed) setError('Não foi possível atualizar notificações.'); }
    }
    const update = () => { void load(); };
    update();
    const timer = window.setInterval(update, 15000);
    window.addEventListener('hub-requests-changed', update);
    window.addEventListener('focus', update);
    return () => { disposed = true; controller.abort(); window.clearInterval(timer); window.removeEventListener('hub-requests-changed', update); window.removeEventListener('focus', update); };
  }, [auth.user.id, auth.user.role, refresh]);
  useEffect(() => {
    if (!open) return;
    const close = (event: PointerEvent) => { if (!region.current?.contains(event.target as Node)) setOpen(false); };
    const escape = (event: KeyboardEvent) => { if (event.key === 'Escape') { setOpen(false); region.current?.querySelector('button')?.focus(); } };
    document.addEventListener('pointerdown', close); document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('pointerdown', close); document.removeEventListener('keydown', escape); };
  }, [open]);
  async function visit(item: HubNotification) {
    if (pending) return;
    setPending(true); setError('');
    try {
      await requestMutation(auth, '/api/notifications/read', { id: item.id });
      setOpen(false); window.location.hash = requestURL(item.requestId);
    } catch (problem) { setError(problem instanceof Error ? problem.message : 'Falha de conexão.'); }
    finally { setPending(false); }
  }
  if (auth.user.role === 'USER') return null;
  return <div className="notification-center" ref={region}>
    <button className="notification-trigger" type="button" aria-expanded={open} aria-controls="hub-notifications" onClick={() => setOpen(value => !value)}>Notificações <span aria-label={`${data?.unreadCount ?? 0} não lidas`}>{data?.unreadCount ?? '…'}</span></button>
    {open ? <section className="notification-panel" id="hub-notifications" aria-label="Central de notificações"><h2>Notificações do hub</h2><p>Ao abrir uma notificação, ela será marcada como lida.</p>{error ? <p className="form-error" role="alert">{error}</p> : null}
      {!data ? <p role="status">Carregando…</p> : data.notifications.length ? <ul>{data.notifications.map(item => <li key={item.id}><button className={item.readAt ? 'read' : 'unread'} type="button" disabled={pending} onClick={() => { void visit(item); }}><strong>{actionLabels[item.action]}{item.readAt ? '' : ' · Não lida'}</strong><span>{item.content}</span><time dateTime={item.createdAt}>{new Date(item.createdAt).toLocaleString('pt-BR')}</time></button></li>)}</ul> : <p>Nenhuma notificação ainda.</p>}
    </section> : null}
  </div>;
}

function RequestColumnFields({ columns, onChange, removable = false }: { columns: RequestedColumn[]; onChange: (columns: RequestedColumn[]) => void; removable?: boolean }) {
  return <div className="initial-columns">{columns.map((column, index) => <div className="initial-column" key={index}>
    <div className="initial-column-heading"><h3>Coluna {index + 1}</h3>{removable ? <button type="button" className="btn tertiary" disabled={columns.length === 1} onClick={() => onChange(columns.filter((_, position) => position !== index))}>Remover coluna {index + 1}</button> : null}</div>
    <div className="form-field"><label htmlFor={`request-column-${index}`}>Nome da coluna {index + 1}</label><input id={`request-column-${index}`} required maxLength={128} pattern="[A-Za-z_][A-Za-z0-9_]*" title="Comece com letra ou _; use apenas letras, números e _." value={column.name} onChange={event => onChange(columns.map((item, position) => position === index ? { ...item, name: event.target.value } : item))} /></div>
    <div className="form-field"><label htmlFor={`request-description-${index}`}>Descrição da coluna {index + 1} (opcional)</label><textarea id={`request-description-${index}`} maxLength={4000} rows={2} value={column.description} onChange={event => onChange(columns.map((item, position) => position === index ? { ...item, description: event.target.value } : item))} /></div>
  </div>)}</div>;
}

function NewColumnRequest({ tableId }: { tableId: string }) {
  const auth = useContext(AuthContext)!;
  const table = useResource<TableDetail>(`/api/tables/${encodeURIComponent(tableId)}`);
  const requests = useResource<{ open: ColumnRequest[]; closed: ColumnRequest[] }>('/api/requests');
  const [reason, setReason] = useState('');
  const [columns, setColumns] = useState<RequestedColumn[]>([{ name: '', description: '' }]);
  const [pending, setPending] = useState(false);
  const busy = useRef(false);
  const [error, setError] = useState('');
  useEffect(() => { document.title = 'Solicitar colunas · Motta-hub'; }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy.current || auth.user.role !== 'FULLSTACK') return;
    busy.current = true; setPending(true); setError('');
    try {
      const result = await requestMutation(auth, '/api/requests', { tableId, reason: reason.trim(), columns: columns.map(column => ({ name: column.name.trim(), description: column.description })) }) as ColumnRequest;
      window.location.hash = requestURL(result.id);
    } catch (problem) { setError(problem instanceof Error ? problem.message : 'Falha de conexão. Confira os pedidos antes de tentar novamente.'); }
    finally { busy.current = false; setPending(false); }
  }
  if (auth.user.role !== 'FULLSTACK') return <div className="empty-state" role="alert"><h1>Acesso restrito</h1><p>Somente FullStack pode solicitar colunas.</p></div>;
  if (table.resource.status === 'loading' || requests.resource.status === 'loading') return <p role="status">Carregando tabela e solicitações…</p>;
  if (table.resource.status === 'error') return <ErrorState retry={table.retry} message={table.resource.message} />;
  if (requests.resource.status === 'error') return <ErrorState retry={requests.retry} message={requests.resource.message} />;
  const existing = requests.resource.data.open.find(request => request.tableId === tableId);
  return <div className="requests-page"><div className="page-heading"><p className="hub-eyebrow">COLABORAÇÃO / CATÁLOGO LOCAL</p><h1>Solicitar colunas</h1><p>{table.resource.data.fullName}</p></div>
    {existing ? <div className="empty-state"><h2>Esta tabela já tem uma solicitação em processamento</h2><p>É permitido um pedido aberto por tabela. Você pode solicitar em outra tabela.</p><a className="back-link" href={requestURL(existing.id)}>Ver solicitação aberta</a></div> : <form className="catalog-form create-form" onSubmit={submit} aria-busy={pending}><fieldset className="form-section" disabled={pending}><legend>Motivo e colunas</legend><p className="form-intro">O DBA decide o pedido inteiro e pode revisar apenas nomes e descrições. A aprovação atualiza o catálogo local; nenhum SQL é executado.</p>
      <div className="form-field"><label htmlFor="request-reason">Motivo da solicitação</label><textarea id="request-reason" required maxLength={4000} value={reason} onChange={event => setReason(event.target.value)} /></div>
      <RequestColumnFields columns={columns} onChange={setColumns} removable />
      <button className="btn secondary" type="button" disabled={columns.length >= 200} onClick={() => setColumns(current => [...current, { name: '', description: '' }])}>Adicionar outra coluna</button>
      {error ? <p className="form-error" role="alert">{error}</p> : null}<button type="submit" className="btn" disabled={!reason.trim()}>{pending ? 'Enviando…' : 'Enviar solicitação'}</button>
    </fieldset></form>}
    <a className="back-link" href={`#/tabelas/${encodeURIComponent(tableId)}`}>Voltar à tabela</a>
  </div>;
}

function RequestDetail({ request, onChanged }: { request: ColumnRequest; onChanged: () => void }) {
  const auth = useContext(AuthContext)!;
  const [mode, setMode] = useState<'EDIT' | 'COMMENT' | 'APPROVE' | 'REJECT' | 'CANCEL' | null>(null);
  const [columns, setColumns] = useState(request.columns);
  const [comment, setComment] = useState('');
  const [pending, setPending] = useState(false);
  const busy = useRef(false);
  const [error, setError] = useState('');
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement | null>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  useEffect(() => { if (mode) { dialog.current?.showModal(); input.current?.focus(); } }, [mode]);
  function dismiss() { if (busy.current) return; dialog.current?.close(); setMode(null); setError(''); trigger.current?.focus(); }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!mode || busy.current) return;
    busy.current = true; setPending(true); setError('');
    try {
      await requestMutation(auth, `/api/requests/${encodeURIComponent(request.id)}`, { action: mode, revision: request.revision, ...(mode === 'EDIT' ? { columns } : mode === 'APPROVE' ? {} : { comment }) });
      dialog.current?.close(); setMode(null); onChanged();
    } catch (problem) { setError(problem instanceof Error ? problem.message : 'Falha de conexão. Atualize antes de tentar novamente.'); }
    finally { busy.current = false; setPending(false); }
  }
  const labels = { EDIT: 'Editar colunas', COMMENT: 'Comentar', APPROVE: 'Aprovar solicitação inteira', REJECT: 'Fechar — recusar', CANCEL: 'Cancelar solicitação' };
  return <article className="request-detail"><div className="request-meta"><span className={`request-badge ${request.status.toLowerCase()}`}>{requestStatusLabels[request.status]}</span>{request.status === 'OPEN' && request.commented ? <span className="request-badge">Comentada · aguarda decisão</span> : null}<span>{request.columns.length} colunas</span></div>
    <h2>{request.tableName}</h2><p className="request-author">Solicitada por {request.author} · <time dateTime={request.createdAt}>{new Date(request.createdAt).toLocaleString('pt-BR')}</time></p><h3>Motivo</h3><p className="request-reason">{request.reason}</p>
    <h3>Colunas solicitadas</h3><div className="column-list">{request.columns.map((column, index) => <div className="column-card" key={index}><h3>{column.name}</h3><p>{column.description || 'Sem descrição.'}</p></div>)}</div>
    <a className="back-link" href={`#/tabelas/${encodeURIComponent(request.tableId)}`}>Ver tabela no catálogo</a>
    {request.status === 'OPEN' ? <div className="request-actions">{(auth.user.role === 'DBA' ? ['EDIT', 'COMMENT', 'APPROVE', 'REJECT'] as const : ['CANCEL'] as const).map(action => <button className={`btn ${action === 'REJECT' || action === 'CANCEL' ? 'danger' : action === 'APPROVE' ? '' : 'secondary'}`} type="button" key={action} onClick={event => { trigger.current = event.currentTarget; setColumns(request.columns); setComment(''); setError(''); setMode(action); }}>{labels[action]}</button>)}</div> : <p className="documentation-notice">Pedido encerrado. O registro e o histórico foram preservados.</p>}
    <section className="request-history" aria-label="Histórico da solicitação"><h3>Últimas 5 ações</h3><ol>{request.history.map(item => <li key={item.id}><div><strong>{actionLabels[item.action] ?? item.action}</strong><time dateTime={item.createdAt}>{new Date(item.createdAt).toLocaleString('pt-BR')}</time></div><small>{item.author}</small><p>{item.content}</p></li>)}</ol></section>
    <dialog ref={dialog} className="column-dialog request-dialog" aria-labelledby="request-action-title" onCancel={event => { event.preventDefault(); dismiss(); }}><h2 id="request-action-title">{mode ? labels[mode] : ''}</h2><p>{request.tableName}</p><form className="catalog-form" onSubmit={submit} aria-busy={pending}><fieldset disabled={pending} className="request-dialog-fields">
      {mode === 'EDIT' ? <><p>Edite somente nome e descrição. A quantidade de colunas, a tabela e o motivo não mudam.</p><RequestColumnFields columns={columns} onChange={setColumns} /></> : mode === 'APPROVE' ? <p>Todas as {request.columns.length} colunas serão adicionadas ao catálogo, junto com a decisão. Não há aprovação parcial e nenhum SQL será executado.</p> : <div className="form-field"><label htmlFor="request-comment">{mode === 'REJECT' ? 'Justificativa obrigatória da recusa' : mode === 'CANCEL' ? 'Comentário obrigatório do cancelamento' : 'Comentário obrigatório'}</label><textarea ref={input} id="request-comment" required maxLength={4000} value={comment} onChange={event => setComment(event.target.value)} /><p className="form-intro">{mode === 'COMMENT' ? 'Comentar mantém a solicitação aberta. FullStack não responde comentários.' : mode === 'CANCEL' ? 'Qualquer FullStack pode cancelar este pedido. Ele será preservado como cancelado, fora das listas.' : 'Fechar significa recusar o pedido inteiro.'}</p></div>}
      {error ? <p className="form-error" role="alert">{error}</p> : null}<div className="form-actions"><button className="btn secondary" type="button" onClick={dismiss}>Voltar</button><button className={`btn ${mode === 'REJECT' || mode === 'CANCEL' ? 'danger' : ''}`} type="submit" disabled={mode !== 'EDIT' && mode !== 'APPROVE' && !comment.trim()}>{pending ? 'Salvando…' : mode ? labels[mode] : 'Confirmar'}</button></div>
    </fieldset></form></dialog>
  </article>;
}

function RequestsPage({ requestId = '' }: { requestId?: string }) {
  const auth = useContext(AuthContext)!;
  const { resource, retry } = useResource<{ open: ColumnRequest[]; closed: ColumnRequest[] } | ColumnRequest>(requestId ? `/api/requests/${encodeURIComponent(requestId)}` : '/api/requests');
  useEffect(() => { document.title = 'Solicitações · Motta-hub'; }, []);
  if (auth.user.role === 'USER') return <div className="empty-state" role="alert"><h1>Acesso restrito</h1><p>Solicitações disponíveis para DBA e FullStack.</p></div>;
  function list(items: ColumnRequest[]) {
    return items.length ? <div className="request-list">{items.map(item => <a className="request-card" key={item.id} href={requestURL(item.id)}><div><span className={`request-badge ${item.status.toLowerCase()}`}>{requestStatusLabels[item.status]}</span>{item.status === 'OPEN' && item.commented ? <span className="request-badge">Comentada</span> : null}</div><h3>{item.tableName}</h3><p>{item.reason}</p><small>{item.columns.length} colunas · {item.author}</small><time dateTime={item.closedAt || item.createdAt}>{new Date(item.closedAt || item.createdAt).toLocaleString('pt-BR')}</time><strong>Ver solicitação →</strong></a>)}</div> : <p className="documentation-notice">Nenhuma solicitação nesta seção.</p>;
  }
  return <div className="requests-page"><div className="heading-actions"><div className="page-heading"><p className="hub-eyebrow">COLABORAÇÃO / CATÁLOGO LOCAL</p><h1>Solicitações de colunas</h1><p>{auth.user.role === 'DBA' ? 'Revise e decida os pedidos de todos os FullStacks.' : 'Acompanhe os pedidos de todos os FullStacks. Para solicitar, abra uma tabela existente.'}</p></div><button className="btn secondary" type="button" onClick={retry}>Atualizar solicitações</button></div>
    {resource.status === 'loading' ? <p role="status">Carregando solicitações…</p> : resource.status === 'error' ? <ErrorState retry={retry} message={resource.message} /> : 'open' in resource.data ? <><section className="hub-section"><h2>{auth.user.role === 'DBA' ? 'Solicitações não respondidas' : 'Solicitações em processamento'} <span className="request-count">{resource.data.open.length}</span></h2><p className="form-intro">Comentários não encerram o pedido. Apenas uma solicitação aberta por tabela.</p>{list(resource.data.open)}</section><section className="hub-section"><h2>Últimas 5 solicitações fechadas</h2><p className="form-intro">Aprovadas e recusadas. Canceladas não aparecem nesta lista.</p>{list(resource.data.closed)}</section></> : <RequestDetail key={`${resource.data.id}:${resource.data.revision}`} request={resource.data} onChanged={retry} />}
    {requestId ? <a className="back-link" href="#/solicitacoes">Voltar às solicitações</a> : <a className="back-link" href="#/tabelas">Explorar tabelas</a>}
  </div>;
}

type SavedScript = { id: string; sql: string; createdAt: string };
function TableScript({ table, creating, onCloseForm }: { table: TableDetail; creating: boolean; onCloseForm: () => void }) {
  const auth = useContext(AuthContext)!;
  const canEdit = auth.user.role === 'DBA';
  const { resource, retry } = useResource<{ scripts: SavedScript[] }>(`/api/tables/${encodeURIComponent(table.id)}/scripts`);
  const [saved, setSaved] = useState<SavedScript[] | null>(null);
  const initialSql = `ALTER TABLE ${table.fullName.split('.').map(part => `\`${part.replaceAll('`', '``')}\``).join('.')} `;
  const [sql, setSql] = useState(initialSql);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const input = useRef<HTMLTextAreaElement>(null);
  const busy = useRef(false);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => { if (creating && input.current) { input.current.focus(); input.current.setSelectionRange(input.current.value.length, input.current.value.length); } }, [creating]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canEdit || busy.current) return;
    busy.current = true; setPending(true); setError(''); setMessage('');
    try {
      const response = await fetch(`/api/tables/${encodeURIComponent(table.id)}/scripts`, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': auth.csrfToken }, body: JSON.stringify({ sql }) });
      if (!mounted.current) return;
      if (response.status === 401) { auth.refresh(); return; }
      if (!response.ok) { const text = await responseError(response, 'Não foi possível validar e salvar o script.'); if (mounted.current) setError(text); return; }
      const result = await response.json() as { scripts: SavedScript[] };
      if (!mounted.current) return;
      setSaved(result.scripts); setSql(initialSql); onCloseForm(); setMessage('Script validado e salvo no catálogo. Nenhum SQL foi executado.');
      document.getElementById('new-script')?.focus();
    } catch { if (mounted.current) setError('Falha de conexão. Confira os scripts cadastrados antes de tentar novamente.'); }
    finally { busy.current = false; if (mounted.current) setPending(false); }
  }
  const scripts = saved ?? (resource.status === 'success' ? resource.data.scripts : []);
  return <section className="table-script" aria-labelledby="script-heading">
    <h2 id="script-heading" className="columns-heading">Scripts de alteração</h2>
    <p className="script-note">Somente ALTER TABLE para <strong>{table.fullName}</strong>. CREATE, DELETE, DROP TABLE e outros comandos são bloqueados. Os scripts ficam documentados aqui: não são executados e não atualizam as colunas automaticamente.</p>
    {canEdit && creating ? <form id="new-script-form" className="catalog-form form-section column-create" aria-label="Novo script de alteração" aria-busy={pending} onSubmit={submit}>
      <div className="form-field"><label htmlFor="alter-script">Script ALTER TABLE</label><textarea ref={input} id="alter-script" className="script-input" required maxLength={20000} rows={8} value={sql} disabled={pending} onChange={event => setSql(event.target.value)} placeholder={`ALTER TABLE ${table.fullName} ADD COLUMN nome_coluna TIPO;`} aria-describedby="alter-script-hint" /></div>
      <p id="alter-script-hint" className="form-intro">Informe schema e tabela em cada comando. Ao salvar, o servidor verifica os comandos e a tabela alvo; isso não garante validade de tipos ou compatibilidade com o banco de origem. Não inclua credenciais ou dados pessoais.</p>
      {error ? <p className="form-error" role="alert">{error}</p> : null}
      <div className="form-actions"><button className="btn" type="submit" disabled={pending || !sql.trim()}>{pending ? 'Validando…' : 'Validar e salvar'}</button><button className="btn tertiary" type="button" disabled={pending} onClick={() => { onCloseForm(); setError(''); document.getElementById('new-script')?.focus(); }}>Cancelar</button></div>
    </form> : null}
    {message ? <p role="status">{message}</p> : null}
    {resource.status === 'loading' && saved === null ? <p role="status">Carregando scripts…</p> : resource.status === 'error' && saved === null ? <ErrorState retry={retry} message={resource.message} /> : scripts.length ? <div className="column-list">{scripts.map(script => <article key={script.id}><p className="script-note">Cadastrado em <time dateTime={script.createdAt}>{new Date(script.createdAt).toLocaleString('pt-BR')}</time> · Somente documentação</p><pre tabIndex={0} aria-label="Script ALTER TABLE cadastrado"><code>{script.sql}</code></pre></article>)}</div> : <p className="result-count">Nenhum script cadastrado para esta tabela.</p>}
  </section>;
}

function TableRemoval({ table, onDeleted }: { table: TableDetail; onDeleted: (name: string) => void }) {
  const auth = useContext(AuthContext)!;
  const [step, setStep] = useState<1 | 2 | null>(null);
  const [confirmation, setConfirmation] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const noButton = useRef<HTMLButtonElement>(null);
  const busy = useRef(false);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    if (step === null) return;
    if (dialog.current && !dialog.current.open) dialog.current.showModal();
    if (step === 1) input.current?.focus();
    else noButton.current?.focus();
  }, [step]);
  function dismiss() {
    if (busy.current) return;
    dialog.current?.close();
    setStep(null); setConfirmation(''); setError('');
    trigger.current?.focus();
  }
  async function remove() {
    if (busy.current || auth.user.role !== 'DBA' || step !== 2 || confirmation !== 'DELeT@R') return;
    busy.current = true; setPending(true); setError('');
    try {
      const response = await fetch(`/api/tables/${encodeURIComponent(table.id)}`, {
        method: 'DELETE', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': auth.csrfToken },
        body: JSON.stringify({ confirmation: 'DELeT@R', confirmed: true }),
      });
      if (!mounted.current) return;
      if (response.status === 401) { auth.refresh(); return; }
      if (!response.ok) {
        const text = await responseError(response, 'Não foi possível excluir a tabela.');
        if (mounted.current) setError(text);
        return;
      }
      dialog.current?.close();
      trigger.current?.focus();
      onDeleted(table.fullName);
    } catch { if (mounted.current) setError('Falha de conexão. Confira o catálogo antes de tentar excluir novamente.'); }
    finally { busy.current = false; if (mounted.current) setPending(false); }
  }
  if (auth.user.role !== 'DBA') return null;
  return <>
    <button ref={trigger} className="btn danger" type="button" disabled={pending} onClick={() => { setConfirmation(''); setError(''); setStep(1); }}>Excluir tabela</button>
    <dialog ref={dialog} className="column-dialog table-delete-dialog" aria-labelledby="delete-table-title" aria-describedby="delete-table-description" aria-busy={pending} onCancel={event => { event.preventDefault(); dismiss(); }} onClose={() => { if (mounted.current && !dialog.current?.open && !busy.current) dismiss(); }}>
      <h2 id="delete-table-title">{step === 2 ? 'Certeza em deletar?' : 'Excluir tabela'}</h2>
      <p id="delete-table-description">Tabela alvo: <strong>{table.fullName}</strong>. A exclusão local é irreversível e remove a documentação, as colunas e os scripts desta tabela do catálogo. Não altera a tabela no banco de origem nem a planilha.</p>
      {step === 1 ? <div className="form-field"><label htmlFor="delete-table-confirmation">Escreva a palavra: "DELeT@R"</label><input ref={input} id="delete-table-confirmation" autoComplete="off" spellCheck={false} value={confirmation} onChange={event => setConfirmation(event.target.value)} aria-describedby="delete-table-hint" /><p id="delete-table-hint" className="form-intro">Use exatamente as letras maiúsculas, minúsculas e símbolos indicados, sem espaços adicionais.</p></div> : null}
      {error ? <p className="form-error" role="alert">{error}</p> : null}
      {pending ? <p role="status">Excluindo tabela… Aguarde a confirmação. Não é possível cancelar uma exclusão em andamento.</p> : null}
      <div className="form-actions">{step === 1 ? <><button className="btn secondary" type="button" onClick={dismiss}>Cancelar</button><button className="btn" type="button" disabled={confirmation !== 'DELeT@R'} onClick={() => { if (confirmation === 'DELeT@R') setStep(2); }}>Continuar</button></> : <><button ref={noButton} className="btn secondary" type="button" disabled={pending} onClick={dismiss}>Não</button><button className="btn danger" type="button" disabled={pending || step !== 2 || confirmation !== 'DELeT@R'} onClick={() => { void remove(); }}>Sim</button></>}</div>
    </dialog>
  </>;
}

function TablePage({ path, term, onDeleted }: { path: string; term: string; onDeleted: (name: string) => void }) {
  const auth = useContext(AuthContext)!;
  const canEdit = auth.user.role === 'DBA';
  const canRequest = auth.user.role === 'FULLSTACK';
  const [creating, setCreating] = useState(false);
  const [creatingScript, setCreatingScript] = useState(false);
  const [view, setView] = useState<'columns' | 'script'>('columns');
  const [updated, setUpdated] = useState<TableDetail | null>(null);
  const { resource, retry } = useResource<TableDetail>(`/api/tables/${path.slice('/tabelas/'.length)}`);
  const table = updated ?? (resource.status === 'success' ? resource.data : null);
  const title = table ? `${table.fullName} · Colunas` : 'Colunas · Motta-hub';
  useEffect(() => { document.title = title; }, [title]);
  if (resource.status === 'loading') return <p className="result-count" role="status">Carregando colunas…</p>;
  if (resource.status === 'error') return resource.code === 404 ? <NotFound term={term} /> : <ErrorState retry={retry} message={resource.message} />;
  const tableId = path.slice('/tabelas/'.length);
  return <>
    <nav className="breadcrumbs" aria-label="Caminho de navegação"><a href={searchURL(term)}>Tabelas</a><span className="separator" aria-hidden="true">›</span><span aria-current="page">{view === 'columns' ? 'Colunas' : 'Script'}</span></nav>
    <div className="heading-actions"><h1 className="detail-title">{table!.fullName}</h1><div className="table-detail-actions">{canRequest ? <a className="btn" href={`#/solicitar-colunas/${encodeURIComponent(tableId)}`}>Solicitar colunas</a> : null}{canEdit ? <>{view === 'columns' ? <button id="new-column" className="btn" type="button" aria-expanded={creating} aria-controls="new-column-form" onClick={() => setCreating(true)}>Nova Coluna</button> : <button id="new-script" className="btn" type="button" aria-expanded={creatingScript} aria-controls="new-script-form" onClick={() => setCreatingScript(true)}>Novo Script</button>}<TableRemoval table={table!} onDeleted={onDeleted} /></> : null}</div></div>
    <div className="view-toggle" role="group" aria-label="Visualização da tabela">
      <button type="button" aria-pressed={view === 'columns'} aria-controls="table-view" onClick={() => setView('columns')}>Colunas</button>
      <button type="button" aria-pressed={view === 'script'} aria-controls="table-view" onClick={() => setView('script')}>Script</button>
    </div>
    <div id="table-view">{view === 'columns' ? <Columns table={table!} onChanged={setUpdated} creating={creating} onCloseForm={() => setCreating(false)} /> : <TableScript table={table!} creating={creatingScript} onCloseForm={() => setCreatingScript(false)} />}</div>
    <a className="back-link" href={searchURL(term)}>Voltar para pesquisa</a>
  </>;
}

type ColumnDraft = { key: number; name: string; description: string };
type TablePayload = { schema: string; name: string; description: string; columns: { name: string; description: string }[] };

const sqlString = String.raw`'(?:[^'\\]|\\.|'')*'`;
const commentPattern = new RegExp(String.raw`\bCOMMENT\s*(?:=\s*)?(${sqlString})`, 'i');
const constraintPattern = /^(?:CONSTRAINT|PRIMARY|FOREIGN|UNIQUE|CHECK|INDEX|KEY|PERIOD|LIKE)\b/i;

function unquoteString(literal: string) {
  return literal.slice(1, -1).replace(/''/g, "'").replace(/\\(.)/g, '$1');
}

function stripSqlComments(sql: string) {
  let output = '';
  for (let i = 0; i < sql.length; i++) {
    const char = sql[i];
    if (char === "'" || char === '"' || char === '`') {
      const start = i;
      for (i++; i < sql.length && sql[i] !== char; i++) if (sql[i] === '\\' && char === "'") i++;
      output += sql.slice(start, i + 1);
    } else if (char === '-' && sql[i + 1] === '-') {
      while (i < sql.length && sql[i] !== '\n') i++;
      output += '\n';
    } else if (char === '/' && sql[i + 1] === '*') {
      const end = sql.indexOf('*/', i + 2);
      i = end === -1 ? sql.length : end + 1;
      output += ' ';
    } else output += char;
  }
  return output;
}

function splitTopLevel(body: string) {
  const parts: string[] = [];
  let depth = 0, start = 0;
  for (let i = 0; i < body.length; i++) {
    const char = body[i];
    if (char === "'" || char === '"' || char === '`') {
      for (i++; i < body.length && body[i] !== char; i++) if (body[i] === '\\' && char === "'") i++;
    } else if (char === '(' || char === '<') depth++;
    else if (char === ')' || char === '>') depth--;
    else if (char === ',' && depth === 0) { parts.push(body.slice(start, i)); start = i + 1; }
  }
  parts.push(body.slice(start));
  return parts.map(part => part.trim()).filter(Boolean);
}

function readIdentifier(text: string) {
  const match = /^\s*(?:`((?:[^`]|``)+)`|"((?:[^"]|"")+)"|\[([^\]]+)\]|([A-Za-z0-9_]+))/.exec(text);
  if (!match) return null;
  const value = match[1]?.replace(/``/g, '`') ?? match[2]?.replace(/""/g, '"') ?? match[3] ?? match[4];
  return { value, rest: text.slice(match[0].length) };
}

function parseCreateTable(sql: string): TablePayload {
  const clean = stripSqlComments(sql).trim().replace(/;\s*$/, '');
  const header = /^CREATE\s+(?:OR\s+REPLACE\s+)?(?:(?:GLOBAL\s+|LOCAL\s+)?(?:TEMPORARY|TEMP|EXTERNAL)\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?/i.exec(clean);
  if (!header) throw new Error('O script deve começar com CREATE TABLE.');
  let rest = clean.slice(header[0].length);
  const nameParts: string[] = [];
  for (;;) {
    const part = readIdentifier(rest);
    if (!part) throw new Error('Não foi possível ler o nome da tabela.');
    nameParts.push(part.value);
    rest = part.rest;
    if (!rest.trimStart().startsWith('.')) break;
    rest = rest.trimStart().slice(1);
  }
  if (nameParts.length < 2) throw new Error('Use o nome qualificado no formato schema.tabela.');
  const [schema, name] = nameParts.slice(-2);
  rest = rest.trimStart();
  if (!rest.startsWith('(')) throw new Error('Não foi possível encontrar a lista de colunas entre parênteses.');
  let depth = 0, end = -1;
  for (let i = 0; i < rest.length; i++) {
    const char = rest[i];
    if (char === "'" || char === '"' || char === '`') {
      for (i++; i < rest.length && rest[i] !== char; i++) if (rest[i] === '\\' && char === "'") i++;
    } else if (char === '(') depth++;
    else if (char === ')' && --depth === 0) { end = i; break; }
  }
  if (end === -1) throw new Error('Os parênteses da lista de colunas não estão fechados.');
  const columns = splitTopLevel(rest.slice(1, end)).flatMap(definition => {
    if (constraintPattern.test(definition)) return [];
    const column = readIdentifier(definition);
    if (!column) throw new Error(`Não foi possível ler a coluna: ${definition.slice(0, 60)}`);
    const comment = commentPattern.exec(column.rest);
    return [{ name: column.value, description: comment ? unquoteString(comment[1]) : '' }];
  });
  const tableComment = commentPattern.exec(rest.slice(end + 1));
  return { schema, name, description: tableComment ? unquoteString(tableComment[1]) : '', columns };
}

function NewTable({ term }: { term: string }) {
  const auth = useContext(AuthContext)!;
  const [schema, setSchema] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [columns, setColumns] = useState<ColumnDraft[]>([]);
  const [mode, setMode] = useState<'form' | 'script'>('form');
  const [script, setScript] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const nextKey = useRef(0);
  const mounted = useRef(true);
  const canCreate = auth.user.role === 'DBA';
  useEffect(() => {
    document.title = 'Nova tabela · Motta-hub';
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  function updateColumn(key: number, field: 'name' | 'description', value: string) {
    setColumns(current => current.map(column => column.key === key ? { ...column, [field]: value } : column));
  }
  let parsed: { table: TablePayload } | { error: string } | null = null;
  if (mode === 'script' && script.trim()) {
    try { parsed = { table: parseCreateTable(script) }; }
    catch (problem) { parsed = { error: problem instanceof Error ? problem.message : 'Script inválido.' }; }
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending || !canCreate) return;
    let payload: TablePayload;
    if (mode === 'script') {
      if (!parsed) { setError('Cole o script CREATE TABLE da tabela.'); return; }
      if ('error' in parsed) { setError(parsed.error); return; }
      payload = parsed.table;
    } else {
      if (!schema.trim() || !name.trim() || columns.some(column => !column.name.trim())) {
        setError('Preencha o schema, o nome da tabela e o nome de cada coluna inicial.');
        return;
      }
      payload = { schema: schema.trim(), name: name.trim(), description: description.trim(), columns: columns.map(column => ({ name: column.name.trim(), description: column.description.trim() })) };
    }
    setPending(true);
    setError('');
    try {
      const response = await fetch('/api/tables', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': auth.csrfToken },
        body: JSON.stringify(payload),
      });
      if (!mounted.current) return;
      if (response.status === 401) { auth.refresh(); return; }
      if (!response.ok) { setError(await responseError(response, 'Não foi possível criar a tabela. Tente novamente.')); return; }
      const table = await response.json() as TableDetail;
      if (mounted.current) window.location.hash = `#/tabelas/${encodeURIComponent(table.id)}?${new URLSearchParams({ name: term })}`;
    } catch { if (mounted.current) setError('Não foi possível criar a tabela. Tente novamente.'); }
    finally { if (mounted.current) setPending(false); }
  }
  if (!canCreate) return <><a className="back-link" href={searchURL(term)}>Voltar para pesquisa</a><div className="empty-state" role="alert"><h1>Acesso restrito</h1><p>Apenas DBA pode criar tabelas no catálogo.</p></div></>;
  return <>
    <nav className="breadcrumbs" aria-label="Caminho de navegação"><a href={searchURL(term)}>Tabelas</a><span className="separator" aria-hidden="true">›</span><span aria-current="page">Nova tabela</span></nav>
    <div className="page-heading"><h1>Nova tabela</h1><p>Cadastre uma tabela preenchendo o formulário ou colando o script de criação.</p></div>
    <div className="view-toggle" role="group" aria-label="Forma de cadastro">
      <button type="button" aria-pressed={mode === 'form'} onClick={() => { setMode('form'); setError(''); }}>Formulário</button>
      <button type="button" aria-pressed={mode === 'script'} onClick={() => { setMode('script'); setError(''); }}>Script</button>
    </div>
    <form className="catalog-form create-form" onSubmit={submit} aria-busy={pending}>
      {mode === 'script' ? <fieldset disabled={pending} className="form-section"><legend>Script da tabela</legend>
        <p className="form-intro">Cole um <code>CREATE TABLE schema.tabela (...)</code>. Os nomes das colunas e os textos em <code>COMMENT '...'</code> viram as descrições. O script não é executado.</p>
        <div className="form-field"><label htmlFor="table-script">Script SQL</label><textarea id="table-script" className="script-input" name="script" rows={12} spellCheck={false} autoComplete="off" placeholder={"CREATE TABLE meu_schema.minha_tabela (\n  id BIGINT COMMENT 'Identificador',\n  status STRING\n) COMMENT 'Descrição da tabela';"} value={script} onChange={event => { setScript(event.target.value); setError(''); }} /></div>
        {parsed && 'table' in parsed ? <div className="script-preview" aria-live="polite">
          <h2>Prévia do cadastro</h2>
          <dl>
            <dt>Tabela</dt><dd>{parsed.table.schema}.{parsed.table.name}</dd>
            <dt>Descrição</dt><dd>{parsed.table.description || 'Sem descrição'}</dd>
            <dt>Colunas</dt><dd>{parsed.table.columns.length}</dd>
          </dl>
          {parsed.table.columns.length ? <ul>{parsed.table.columns.map((column, index) => <li key={index}><strong>{column.name}</strong>{column.description ? ` — ${column.description}` : ''}</li>)}</ul> : null}
        </div> : parsed ? <p className="form-hint-error" aria-live="polite">{parsed.error}</p> : null}
      </fieldset> : <>
      <fieldset disabled={pending} className="form-section"><legend>Dados da tabela</legend>
        <div className="field-grid">
          <div className="form-field"><label htmlFor="table-schema">Schema</label><input id="table-schema" name="schema" required autoComplete="off" value={schema} onChange={event => setSchema(event.target.value)} /></div>
          <div className="form-field"><label htmlFor="table-name">Nome da tabela</label><input id="table-name" name="name" required autoComplete="off" value={name} onChange={event => setName(event.target.value)} /></div>
        </div>
        <div className="form-field"><label htmlFor="table-description">Descrição <span className="optional">(opcional)</span></label><textarea id="table-description" name="description" rows={3} value={description} onChange={event => setDescription(event.target.value)} /></div>
      </fieldset>
      <fieldset disabled={pending} className="form-section"><legend>Colunas iniciais <span className="optional">(opcional)</span></legend>
        <p className="form-intro">As colunas abaixo serão cadastradas junto com a nova tabela.</p>
        {columns.length ? <div className="initial-columns">{columns.map((column, index) => <div className="initial-column" key={column.key}>
          <div className="initial-column-heading"><h2>Coluna {index + 1}</h2><button className="btn tertiary" type="button" aria-label={`Remover coluna inicial ${index + 1}`} onClick={() => setColumns(current => current.filter(item => item.key !== column.key))}>Remover</button></div>
          <div className="form-field"><label htmlFor={`column-name-${column.key}`}>Nome da coluna</label><input id={`column-name-${column.key}`} required autoComplete="off" value={column.name} onChange={event => updateColumn(column.key, 'name', event.target.value)} /></div>
          <div className="form-field"><label htmlFor={`column-description-${column.key}`}>Descrição <span className="optional">(opcional)</span></label><textarea id={`column-description-${column.key}`} rows={2} value={column.description} onChange={event => updateColumn(column.key, 'description', event.target.value)} /></div>
        </div>)}</div> : <p className="form-intro">Nenhuma coluna inicial adicionada.</p>}
        <button className="btn secondary" type="button" onClick={() => { const key = nextKey.current++; setColumns(current => [...current, { key, name: '', description: '' }]); }}>Adicionar coluna inicial</button>
      </fieldset>
      </>}
      {error ? <p className="form-error" role="alert">{error}</p> : null}
      <div className="form-actions"><button className="btn" type="submit" disabled={pending}>{pending ? 'Criando tabela…' : 'Criar tabela'}</button><a className="back-link" href={searchURL(term)}>Voltar para pesquisa</a></div>
    </form>
  </>;
}

function App() {
  const auth = useContext(AuthContext)!;
  const hash = useSyncExternalStore(subscribeToRoute, readHash);
  const [revision, setRevision] = useState(0);
  const { resource: documentationResource, retry: retryDocumentations } = useResource<DocumentationCatalog>('/api/documentations');
  const [documentChanges, setDocumentChanges] = useState<Documentation[] | null>(null);
  const documents = documentChanges ?? (documentationResource.status === 'success' ? documentationResource.data.documents : []);
  const [sectionChanges, setSectionChanges] = useState<string[]>([]);
  const documentationSchemas = [...new Set([...(documentationResource.status === 'success' ? documentationResource.data.schemas : []), ...documents.map(item => item.schema), ...sectionChanges])];
  async function saveDocumentationCatalog(nextDocuments: Documentation[], nextSchemas = documentationSchemas) {
    const response = await fetch('/api/documentations', {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': auth.csrfToken },
      body: JSON.stringify({ schemas: nextSchemas, documents: nextDocuments }),
    });
    if (response.status === 401) { auth.refresh(); throw new Error('Sua sessão expirou. Entre novamente e tente salvar.'); }
    if (!response.ok) throw new Error(await responseError(response, 'Não foi possível salvar o catálogo de documentações.'));
    setDocumentChanges(nextDocuments);
    const originalSchemas = documentationResource.status === 'success' ? documentationResource.data.schemas : [];
    setSectionChanges(nextSchemas.filter(value => !originalSchemas.includes(value)));
  }
  const [deletionNotice, setDeletionNotice] = useState<{ target: string; name: string } | null>(null);
  const [route, routeAnchor = ''] = (hash.slice(1) || '/inicio').split('#');
  const [path, query = ''] = route.split('?');
  const routeParameters = new URLSearchParams(query);
  const term = routeParameters.get('name') || '';
  const documentationSchema = routeParameters.get('schema') || '';
  const documentationId = routeParameters.get('document') || '';
  const documentationAnchor = routeParameters.get('anchor') || decodedAnchor(routeAnchor);
  function documentationURL(value: string, schema: string) {
    const parameters = new URLSearchParams();
    if (value) parameters.set('name', value);
    if (schema) parameters.set('schema', schema);
    if (documentationId) parameters.set('document', documentationId);
    if (documentationAnchor) parameters.set('anchor', documentationAnchor);
    return '#/documentacoes' + (parameters.size ? `?${parameters}` : '');
  }
  function changeDocumentationSchema(schema: string) {
    window.location.hash = documentationURL(term, schema);
  }
  const isCatalog = path === '/tabelas';
  const isDocumentation = path === '/documentacoes';
  const isHome = ['/', '/inicio'].includes(path);
  function search(value: string, live = false) {
    const target = isDocumentation ? documentationURL(value, documentationSchema) : searchURL(value);
    if (live && (isCatalog || isDocumentation)) {
      window.history.replaceState(null, '', target);
      window.dispatchEvent(new HashChangeEvent('hashchange'));
    } else if (window.location.hash === target) setRevision(version => version + 1);
    else window.location.hash = target;
  }
  function deleted(name: string) {
    const target = searchURL(term);
    setDeletionNotice({ target, name });
    search(term);
  }
  return <Shell term={term} onSearch={search} hash={path}>
    {isCatalog && deletionNotice?.target === hash ? <p role="status">Tabela {deletionNotice.name} excluída do catálogo local. A documentação, as colunas e os scripts foram removidos; a origem e a planilha não foram alteradas.</p> : null}
    {isHome ? <Home /> : isCatalog ? <Catalog key={`${path}:${revision}`} term={term} onSearch={search} /> :
      isDocumentation ? documentationResource.status === 'loading' ? <p role="status">Carregando documentações…</p> : documentationResource.status === 'error' ? <div className="empty-state" role="alert"><h1>Não foi possível carregar as documentações</h1><button className="btn secondary" type="button" onClick={retryDocumentations}>Tentar novamente</button></div> : <Documentations documents={documents} documentationSchemas={documentationSchemas} onChanged={saveDocumentationCatalog} onSectionCreated={name => saveDocumentationCatalog(documents, [...documentationSchemas, name])} term={term} onSearch={search} schema={documentationSchema} onSchemaChange={changeDocumentationSchema} documentId={documentationId} anchor={documentationAnchor} /> :
      path === '/nova-tabela' ? <NewTable term={term} /> :
        path === '/solicitacoes' ? <RequestsPage key={`solic:${revision}`} /> :
          /^\/solicitacoes\/[^/]+$/.test(path) ? <RequestsPage key={path} requestId={decodeURIComponent(path.slice('/solicitacoes/'.length))} /> :
            path === '/solicitar-colunas' || /^\/solicitar-colunas\/[^/]+$/.test(path) ? <NewColumnRequest key={path} tableId={decodeURIComponent(path.slice('/solicitar-colunas/'.length))} /> :
              /^\/tabelas\/[^/]+$/.test(path) ? <TablePage key={path} path={path} term={term} onDeleted={deleted} /> : <NotFound term={term} />}
  </Shell>;
}

createRoot(document.getElementById('root')!).render(<AuthGate><App /></AuthGate>);
