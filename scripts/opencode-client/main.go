// opencode-client — minimal CLI to talk to a local `opencode serve` via opencode-sdk-go.
//
// Usage:
//   opencode-client list                       # list sessions
//   opencode-client prompt "your message"      # create session + send prompt
//   opencode-client prompt -s sesXXX "msg"     # send prompt into existing session
//
// Env:
//   OPENCODE_BASE_URL  default http://127.0.0.1:4096  (matches `opencode serve` default)
//   OPENCODE_API_KEY   if set, sent as `Authorization: Bearer <key>`
//   OPENCODE_MODEL     default claude-sonnet-4-5
//   OPENCODE_PROVIDER  default anthropic

package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"time"

	"github.com/sst/opencode-sdk-go"
	"github.com/sst/opencode-sdk-go/option"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}

	baseURL := envOr("OPENCODE_BASE_URL", "http://127.0.0.1:4096")
	opts := []option.RequestOption{option.WithBaseURL(baseURL)}
	if key := os.Getenv("OPENCODE_API_KEY"); key != "" {
		opts = append(opts, option.WithHeader("Authorization", "Bearer "+key))
	}
	client := opencode.NewClient(opts...)
	ctx := context.Background()

	switch os.Args[1] {
	case "list":
		sessions, err := client.Session.List(ctx, opencode.SessionListParams{})
		check(err)
		dump(sessions)

	case "prompt":
		fs := flag.NewFlagSet("prompt", flag.ExitOnError)
		sessionID := fs.String("s", "", "existing session id (omit to create new)")
		title := fs.String("t", "cli prompt", "title for new session")
		fromFile := fs.String("f", "", "read prompt body from file (use '-' for stdin)")
		systemFile := fs.String("sys", "", "read system prompt from file")
		check(fs.Parse(os.Args[2:]))

		var text string
		switch {
		case *fromFile == "-":
			b, err := io.ReadAll(os.Stdin)
			check(err)
			text = string(b)
		case *fromFile != "":
			b, err := os.ReadFile(*fromFile)
			check(err)
			text = string(b)
		case fs.NArg() > 0:
			text = fs.Arg(0)
		default:
			fmt.Fprintln(os.Stderr, "error: provide prompt text, -f file, or -f -")
			os.Exit(2)
		}

		var systemPrompt string
		if *systemFile != "" {
			b, err := os.ReadFile(*systemFile)
			check(err)
			systemPrompt = string(b)
		}

		if *sessionID == "" {
			s, err := client.Session.New(ctx, opencode.SessionNewParams{
				Title: opencode.F(*title),
			})
			check(err)
			*sessionID = s.ID
			fmt.Fprintf(os.Stderr, "created session: %s\n", s.ID)
		}

		params := opencode.SessionPromptParams{
			Model: opencode.F(opencode.SessionPromptParamsModel{
				ProviderID: opencode.F(envOr("OPENCODE_PROVIDER", "anthropic")),
				ModelID:    opencode.F(envOr("OPENCODE_MODEL", "claude-sonnet-4-5")),
			}),
			Parts: opencode.F([]opencode.SessionPromptParamsPartUnion{
				opencode.TextPartInputParam{
					Type: opencode.F(opencode.TextPartInputTypeText),
					Text: opencode.F(text),
				},
			}),
		}
		if systemPrompt != "" {
			params.System = opencode.F(systemPrompt)
		}
		// Long ctx for big-context reasoning runs.
		promptCtx, cancel := context.WithTimeout(ctx, 30*time.Minute)
		defer cancel()
		resp, err := client.Session.Prompt(promptCtx, *sessionID, params)
		check(err)
		dump(resp)

	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, `usage:
  opencode-client list
  opencode-client prompt [-s sessionID] [-t title] "text"`)
}

func envOr(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func check(err error) {
	if err == nil {
		return
	}
	var apierr *opencode.Error
	if errAs(err, &apierr) {
		fmt.Fprintln(os.Stderr, string(apierr.DumpRequest(true)))
		fmt.Fprintln(os.Stderr, string(apierr.DumpResponse(true)))
	}
	fmt.Fprintln(os.Stderr, "error:", err)
	os.Exit(1)
}

// errAs avoids importing "errors" just for one call.
func errAs(err error, target **opencode.Error) bool {
	t, ok := err.(*opencode.Error)
	if !ok {
		return false
	}
	*target = t
	return true
}

func dump(v any) {
	b, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		fmt.Printf("%+v\n", v)
		return
	}
	fmt.Println(string(b))
}
