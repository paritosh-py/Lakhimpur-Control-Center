package org.lakhimpur.rescueteam;

import android.app.Activity;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.view.WindowInsets;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.Objects;

/** Thin WebView host: all prediction and team functionality stays in the shared web app. */
public class MainActivity extends Activity {
    private WebView web;
    private EditText address;
    private TextView status;
    private String origin;
    private String loadedUrl;

    @Override public void onCreate(Bundle savedState) {
        super.onCreate(savedState);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setBackgroundColor(Color.rgb(17,22,25));
        // Target SDK 36 draws edge-to-edge; reserve system bars and the keyboard explicitly.
        layout.setOnApplyWindowInsetsListener((v,insets) -> {
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.ime());
                v.setPadding(bars.left,bars.top,bars.right,bars.bottom);
            } else {
                v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
        LinearLayout connection = new LinearLayout(this);
        connection.setPadding(dp(12),dp(8),dp(12),dp(8));
        address = new EditText(this);
        address.setSingleLine(true);
        address.setTextSize(14);
        address.setHint(R.string.address_hint);
        address.setContentDescription(getString(R.string.address_label));
        address.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_URI);
        address.setText(getPreferences(MODE_PRIVATE).getString("server_url", ""));
        connection.addView(address,new LinearLayout.LayoutParams(0,dp(52),1));
        Button connect = new Button(this); connect.setText(R.string.open_server);
        connect.setOnClickListener(v -> connect());
        connection.addView(connect,new LinearLayout.LayoutParams(dp(80),dp(52)));
        layout.addView(connection);
        status = new TextView(this);
        status.setPadding(dp(16),dp(8),dp(16),dp(8));
        status.setTextColor(Color.rgb(255,228,170));
        status.setText(R.string.setup_instruction);
        layout.addView(status);
        web = new WebView(this);
        web.setBackgroundColor(Color.rgb(17,22,25));
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);
        settings.setSupportMultipleWindows(false);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                boolean blocked = !Objects.equals(origin,originOf(request.getUrl()));
                if (blocked) status.setText(R.string.external_blocked);
                return blocked;
            }
            @Override public void onPageFinished(WebView view,String url) {
                // Do not replace an error message or mislabel model data as live.
                if (web.getVisibility() == View.VISIBLE) status.setText("Connected to command server · Lakhimpur Team");
            }
            @Override public void onReceivedError(WebView view,WebResourceRequest request,WebResourceError error) {
                if (request.isForMainFrame()) unavailable();
            }
            @Override public void onReceivedHttpError(WebView view,WebResourceRequest request,WebResourceResponse response) {
                if (request.isForMainFrame()) unavailable();
            }
        });
        // No JavaScript/native bridge, certificate bypass or device permissions are needed.
        layout.addView(web,new LinearLayout.LayoutParams(-1,0,1));
        setContentView(layout);
        if (android.os.Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT, () -> {
                if (web.canGoBack()) web.goBack(); else finish();
            });
        }
        if (!address.getText().toString().trim().isEmpty()) connect();
    }

    private void connect() {
        Uri entered = Uri.parse(address.getText().toString().trim());
        if (originOf(entered) == null || entered.getUserInfo() != null) {
            status.setText(R.string.invalid_address);
            return;
        }
        origin = originOf(entered);
        // A bare server address opens team navigation; full Team App links keep their token.
        if (entered.getPath() == null || entered.getPath().isEmpty() || entered.getPath().equals("/")) {
            entered = entered.buildUpon().path("/team-mobile").build();
        }
        if (entered.getQueryParameter("view") == null) entered = entered.buildUpon().appendQueryParameter("view","team").build();
        loadedUrl = entered.toString();
        // Persist the server only, never a team's capability token.
        getPreferences(MODE_PRIVATE).edit().putString("server_url",origin).apply();
        status.setText("Connecting…");
        web.setVisibility(View.VISIBLE);
        web.loadUrl(loadedUrl);
        address.clearFocus();
        ((android.view.inputmethod.InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(address.getWindowToken(),0);
    }

    private String originOf(Uri uri) {
        if (!("http".equals(uri.getScheme()) || "https".equals(uri.getScheme())) || uri.getHost() == null) return null;
        return uri.getScheme()+"://"+uri.getHost()+(uri.getPort() == -1 ? "" : ":"+uri.getPort());
    }
    private void unavailable() {
        web.setVisibility(View.GONE);
        status.setText(R.string.unavailable);
    }
    private int dp(int value) { return Math.round(value*getResources().getDisplayMetrics().density); }
    // API 33+ uses the registered OnBackInvokedCallback above. This is only the
    // API 26-32 fallback; lint cannot infer the runtime registration.
    @android.annotation.SuppressLint("GestureBackNavigation")
    @SuppressWarnings("deprecation") @Override public void onBackPressed() {
        if (web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
    @Override protected void onDestroy() {
        if (web != null) { web.stopLoading(); web.destroy(); }
        super.onDestroy();
    }
}
